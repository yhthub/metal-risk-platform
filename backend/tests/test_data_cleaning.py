"""Real table fixtures and API contracts; no model, corpus, or remote calls."""
import csv
import asyncio
from io import BytesIO, StringIO
import json
import re
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile
from xml.etree import ElementTree as ET

from fastapi import FastAPI
from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.api.data_cleaning import router
from app.security import ApiGuard
from app.services import data_cleaning_service as cleaning
from app.services import data_service
from app.services.data_service import OUTCOME_CONFIGS, _build_analysis, _get_required_columns
import pandas as pd


def csv_bytes(headers, rows):
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


def xlsx_bytes(rows, second_sheet=None):
    workbook = Workbook()
    for row in rows:
        workbook.active.append(row)
    if second_sheet is not None:
        extra = workbook.create_sheet("ignored")
        for row in second_sheet:
            extra.append(row)
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def options(**overrides):
    return json.dumps({"mode": "custom", **overrides})


def valid_system_row(identifier="0007", **changes):
    config = OUTCOME_CONFIGS["blood_pressure"]
    row = {column: "1" for column in _get_required_columns(config)}
    row[config["identifier_column"]] = identifier
    for column in config["outcome_columns"]["sbp"]:
        row[column] = "120"
    for column in config["outcome_columns"]["dbp"]:
        row[column] = "75"
    age_column = next(item["column"] for item in config["confounders"] if item["key"] == "age")
    row[age_column] = "35"
    row.update(changes)
    return row


def system_fixture(rows):
    headers = cleaning.get_cleaning_schema()["required_columns"]
    return csv_bytes(headers, [[row[column] for column in headers] for row in rows])


def system_options(**changes):
    return json.dumps({"mode": "system", "confirm_system_semantics": True, **changes})


def exported_records(payload):
    return list(csv.reader(StringIO(payload.decode("utf-8-sig"), newline="")))


def misleading_dimension(payload, dimension):
    source = BytesIO(payload)
    output = BytesIO()
    with ZipFile(source) as archive, ZipFile(output, "w", compression=ZIP_DEFLATED) as rewritten:
        for item in archive.infolist():
            content = archive.read(item.filename)
            if item.filename == "xl/worksheets/sheet1.xml":
                replacement = b"" if dimension is None else f'<dimension ref="{dimension}"/>'.encode()
                content = re.sub(rb'<dimension\b[^>]*/>', replacement, content)
            rewritten.writestr(item, content)
    return output.getvalue()


def shared_strings_fixture(value, references=3):
    """A real sharedStrings.xml fixture: many cell refs, only one stored text."""
    main_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    types_ns = "http://schemas.openxmlformats.org/package/2006/content-types"
    rels_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    payload = xlsx_bytes([["value"], *[[value] for _ in range(references)]])
    shared = ET.Element(f"{{{main_ns}}}sst", count=str(references), uniqueCount="1")
    ET.SubElement(ET.SubElement(shared, f"{{{main_ns}}}si"), f"{{{main_ns}}}t").text = value
    output = BytesIO()
    with ZipFile(BytesIO(payload)) as archive, ZipFile(output, "w", compression=ZIP_DEFLATED) as rewritten:
        for item in archive.infolist():
            content = archive.read(item.filename)
            if item.filename == "xl/worksheets/sheet1.xml":
                root = ET.fromstring(content)
                for cell in root.iter(f"{{{main_ns}}}c"):
                    address = cell.attrib.get("r", "")
                    if address != "A1":
                        cell.clear()
                        cell.attrib.update(r=address, t="s")
                        ET.SubElement(cell, f"{{{main_ns}}}v").text = "0"
                content = ET.tostring(root, encoding="utf-8")
            elif item.filename == "[Content_Types].xml":
                root = ET.fromstring(content)
                ET.SubElement(root, f"{{{types_ns}}}Override", PartName="/xl/sharedStrings.xml",
                              ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml")
                content = ET.tostring(root, encoding="utf-8")
            elif item.filename == "xl/_rels/workbook.xml.rels":
                root = ET.fromstring(content)
                ET.SubElement(root, f"{{{rels_ns}}}Relationship", Id="rIdSharedFixture",
                              Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings",
                              Target="sharedStrings.xml")
                content = ET.tostring(root, encoding="utf-8")
            rewritten.writestr(item, content)
        rewritten.writestr("xl/sharedStrings.xml", ET.tostring(shared, encoding="utf-8"))
    return output.getvalue()


class SchemaAndOptionsTests(unittest.TestCase):
    def test_schema_is_derived_from_current_analysis_configuration(self):
        schema = cleaning.get_cleaning_schema()
        self.assertEqual(schema["required_columns"], _get_required_columns(OUTCOME_CONFIGS["blood_pressure"]))
        self.assertEqual(len(schema["required_columns"]), 20)
        self.assertEqual([item["column"] for item in schema["fields"] if item["required"]], schema["required_columns"])
        units = {item["column"]: item["unit"] for item in schema["fields"]}
        self.assertEqual(units["PBCD_J__LBXBPB"], "μg/dL")
        self.assertEqual(units["BPXO_J__BPXOSY1"], "mmHg")

    def test_unknown_outcome_is_rejected(self):
        with self.assertRaises(cleaning.CleaningError):
            cleaning.get_cleaning_schema("unknown")

    def test_options_reject_malformed_json_and_non_objects(self):
        for content in ("{", "[]", "null", "42"):
            with self.subTest(content=content), self.assertRaises(cleaning.CleaningError):
                cleaning.parse_options(content)

    def test_options_never_silently_coerce_boolean_or_row_numbers(self):
        for changes in ({"trim_text": "false"}, {"row_start": "1"}, {"row_start": True},
                        {"unknown": 1}, {"filters": [{"column": "a", "operator": "eval", "value": "1"}]}):
            with self.subTest(changes=changes), self.assertRaises(cleaning.CleaningError):
                cleaning.parse_options(options(**changes))

    def test_mapping_collisions_and_inverted_ranges_are_rejected(self):
        cases = [
            {"columns": [{"source": "a", "target": "x"}, {"source": "a", "target": "y"}]},
            {"columns": [{"source": "a", "target": "x"}, {"source": "b", "target": " x "}]},
            {"columns": [{"source": "a", "target": " "}]},
            {"row_start": 3, "row_end": 2},
        ]
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(cleaning.CleaningError):
                cleaning.parse_options(options(**changes))

    def test_option_size_is_bounded(self):
        with self.assertRaises(cleaning.CleaningError):
            cleaning.parse_options(" " * (cleaning.MAX_OPTIONS_BYTES + 1))


class TableReadingTests(unittest.TestCase):
    def test_csv_preserves_ids_na_strings_blank_values_and_quotes(self):
        payload = csv_bytes(["ID", "value", "note"], [["0007", "NA", "A,B\nC"], ["0008", "", "None"]])
        preview = cleaning.inspect_table(payload, "../private.CSV")
        self.assertEqual(preview["filename"], "private.CSV")
        self.assertEqual(preview["preview"][0], {"ID": "0007", "value": "NA", "note": "A,B\nC"})
        self.assertEqual(preview["preview"][1]["value"], "")
        self.assertEqual(preview["total_rows"], 2)

    def test_gb18030_encoding_is_supported_and_reported(self):
        result = cleaning.inspect_table("编号,姓名\r\n0001,测试\r\n".encode("gb18030"), "fixture.csv")
        self.assertEqual(result["preview"][0]["姓名"], "测试")
        self.assertTrue(any("GB18030" in value for value in result["warnings"]))

    def test_duplicate_and_empty_headers_are_not_mangled(self):
        for header in (["a", "a"], ["a", " a "], ["", "b"]):
            with self.subTest(header=header), self.assertRaises(cleaning.CleaningError):
                cleaning.inspect_table(csv_bytes(header, [["1", "2"]]), "fixture.csv")

    def test_header_whitespace_is_normalized_and_reported(self):
        result = cleaning.inspect_table(csv_bytes([" ID "], [["0001"]]), "fixture.csv")
        self.assertEqual(result["columns"], ["ID"])
        self.assertTrue(result["warnings"])

    def test_missing_trailing_cells_are_blank_not_imputed(self):
        result = cleaning.inspect_table(b"a,b,c\n1,2\n", "fixture.csv")
        self.assertEqual(result["preview"][0], {"a": "1", "b": "2", "c": ""})
        self.assertTrue(result["warnings"])

    def test_long_rows_or_unclosed_quotes_are_rejected(self):
        for payload in (b"a,b\n1,2,3\n", b'a,b\n"unfinished,2\n'):
            with self.subTest(payload=payload), self.assertRaises(cleaning.CleaningError):
                cleaning.inspect_table(payload, "fixture.csv")

    def test_only_csv_and_xlsx_are_supported(self):
        for name in ("fixture.xls", "fixture.exe", "fixture.txt"):
            with self.subTest(name=name), self.assertRaises(cleaning.CleaningError):
                cleaning.inspect_table(b"a\n1\n", name)

    def test_empty_file_and_bad_binary_are_rejected(self):
        for payload, name in ((b"", "fixture.csv"), (b"a\x00b", "fixture.csv"), (b"not zip", "fixture.xlsx")):
            with self.subTest(name=name), self.assertRaises(cleaning.CleaningError):
                cleaning.inspect_table(payload, name)

    def test_file_rows_and_columns_have_hard_bounds(self):
        with patch.object(cleaning, "MAX_FILE_BYTES", 3), self.assertRaises(cleaning.CleaningError) as context:
            cleaning.inspect_table(b"a\n1\n", "fixture.csv")
        self.assertEqual(context.exception.status_code, 413)
        with patch.object(cleaning, "MAX_ROWS", 1), self.assertRaises(cleaning.CleaningError):
            cleaning.inspect_table(b"a\n1\n2\n", "fixture.csv")
        with patch.object(cleaning, "MAX_COLUMNS", 1), self.assertRaises(cleaning.CleaningError):
            cleaning.inspect_table(b"a,b\n1,2\n", "fixture.csv")

    def test_preview_is_bounded_but_total_count_is_exact(self):
        result = cleaning.inspect_table(csv_bytes(["id"], [[str(value)] for value in range(30)]), "fixture.csv")
        self.assertEqual(result["total_rows"], 30)
        self.assertEqual(len(result["preview"]), cleaning.PREVIEW_ROWS)

    def test_csv_total_cells_and_per_cell_text_are_bounded(self):
        payload = csv_bytes(["a", "b"], [["1", "2"], ["3", "4"]])
        with patch.object(cleaning, "MAX_TOTAL_CELLS", 3), self.assertRaises(cleaning.CleaningError):
            cleaning.inspect_table(payload, "fixture.csv")
        with patch.object(cleaning, "MAX_CELL_CHARS", 2), self.assertRaises(cleaning.CleaningError):
            cleaning.inspect_table(b"a\n123\n", "fixture.csv")

    def test_xlsx_text_ids_first_sheet_and_formulas_are_preserved(self):
        payload = xlsx_bytes([["ID", "value"], ["0007", "=1+1"]], [["wrong"], ["discard"]])
        result = cleaning.inspect_table(payload, "fixture.xlsx")
        self.assertEqual(result["preview"], [{"ID": "0007", "value": "=1+1"}])
        self.assertTrue(any("第一个工作表" in note for note in result["warnings"]))

    def test_xlsx_dimensions_and_expanded_archive_are_bounded(self):
        payload = xlsx_bytes([["a", "b"], ["1", "2"]])
        with patch.object(cleaning, "MAX_COLUMNS", 1), self.assertRaises(cleaning.CleaningError):
            cleaning.inspect_table(payload, "fixture.xlsx")
        with patch.object(cleaning, "MAX_ROWS", 0), self.assertRaises(cleaning.CleaningError):
            cleaning.inspect_table(payload, "fixture.xlsx")
        with patch.object(cleaning, "MAX_EXPANDED_BYTES", 20), self.assertRaises(cleaning.CleaningError):
            cleaning.inspect_table(payload, "fixture.xlsx")

    def test_xlsx_macro_archives_are_rejected_without_execution(self):
        output = BytesIO()
        with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("xl/vbaProject.bin", b"macro")
        with self.assertRaises(cleaning.CleaningError):
            cleaning.inspect_table(output.getvalue(), "fixture.xlsx")

    def test_xlsx_total_cells_and_per_cell_text_are_bounded(self):
        payload = xlsx_bytes([["a", "b"], ["123", "2"], ["3", "4"]])
        with patch.object(cleaning, "MAX_TOTAL_CELLS", 3), self.assertRaises(cleaning.CleaningError):
            cleaning.inspect_table(payload, "fixture.xlsx")
        with patch.object(cleaning, "MAX_CELL_CHARS", 2), self.assertRaises(cleaning.CleaningError):
            cleaning.inspect_table(payload, "fixture.xlsx")

    def test_xlsx_understated_overstated_or_missing_dimensions_do_not_truncate(self):
        payload = xlsx_bytes([["id", "value"], *[[f"{value:03d}", value] for value in range(1, 6)]])
        for dimension in ("A1:B2", "A1:XFD1048576", None):
            with self.subTest(dimension=dimension):
                result = cleaning.inspect_table(misleading_dimension(payload, dimension), "fixture.xlsx")
                self.assertEqual(result["total_rows"], 5)
                self.assertEqual([row["id"] for row in result["preview"]], ["001", "002", "003", "004", "005"])

    def test_xlsx_actual_row_column_and_cell_limits_apply_with_small_dimension(self):
        payload = misleading_dimension(xlsx_bytes([["id", "value"], ["1", "x"], ["2", "y"], ["3", "z"]]), "A1:A1")
        with patch.object(cleaning, "MAX_ROWS", 2), self.assertRaises(cleaning.CleaningError):
            cleaning.inspect_table(payload, "fixture.xlsx")
        with patch.object(cleaning, "MAX_COLUMNS", 1), self.assertRaises(cleaning.CleaningError):
            cleaning.inspect_table(payload, "fixture.xlsx")
        with patch.object(cleaning, "MAX_TOTAL_CELLS", 5), self.assertRaises(cleaning.CleaningError):
            cleaning.inspect_table(payload, "fixture.xlsx")

    def test_csv_and_xlsx_logical_text_budgets_include_repeated_values(self):
        repeated = "same long text"
        csv_payload = csv_bytes(["value"], [[repeated], [repeated], [repeated]])
        xlsx_payload = xlsx_bytes([["value"], [repeated], [repeated], [repeated]])
        for payload, filename in ((csv_payload, "fixture.csv"), (xlsx_payload, "fixture.xlsx")):
            with self.subTest(filename=filename), patch.object(cleaning, "MAX_LOGICAL_TEXT_BYTES", 30), self.assertRaises(cleaning.CleaningError):
                cleaning.inspect_table(payload, filename)

    def test_xlsx_shared_string_references_count_towards_logical_text_budget(self):
        repeated = "a shared text stored once"
        payload = shared_strings_fixture(repeated, references=3)
        result = cleaning.inspect_table(payload, "shared.xlsx")
        self.assertEqual([row["value"] for row in result["preview"]], [repeated] * 3)
        with patch.object(cleaning, "MAX_LOGICAL_TEXT_BYTES", 50), self.assertRaises(cleaning.CleaningError):
            cleaning.inspect_table(payload, "shared.xlsx")


class TransformTests(unittest.TestCase):
    def test_ranges_are_original_records_before_blank_removal(self):
        payload = b"id,value\n001,1\n\n003,3\n004,4\n"
        result = cleaning.preview_table(payload, "fixture.csv", options(row_start=2, row_end=3))
        self.assertEqual(result["original_rows"], 4)
        self.assertEqual(result["preview"], [{"id": "003", "value": "3"}])
        self.assertEqual([(entry["before"], entry["after"]) for entry in result["audit"] if entry["removed"]], [(4, 2), (2, 1)])

    def test_mapping_order_trim_filter_blank_and_dedup_audits_reconcile(self):
        payload = csv_bytes(["id", "value", "discard"], [
            [" 001 ", " 2 ", "a"], ["001", "2", "b"], ["002", "1", "c"], ["", "", "notblank"]
        ])
        result = cleaning.preview_table(payload, "fixture.csv", options(
            columns=[{"source": "value", "target": "measurement"}, {"source": "id", "target": "participant"}],
            filters=[{"column": "value", "operator": "gte", "value": "2"}], drop_duplicates=True))
        self.assertEqual(result["columns"], ["measurement", "participant"])
        self.assertEqual(result["preview"], [{"measurement": "2", "participant": "001"}])
        self.assertEqual(sum(entry["removed"] for entry in result["audit"]), result["original_rows"] - result["total_rows"])
        self.assertEqual(next(entry for entry in result["audit"] if entry["action"] == "trim_text")["changed_cells"], 2)

    def test_blank_rows_are_evaluated_on_selected_output_columns(self):
        payload = csv_bytes(["value", "discard"], [["", "keep-source"], ["0", ""]])
        result = cleaning.preview_table(payload, "fixture.csv", options(columns=[{"source": "value", "target": "value"}]))
        self.assertEqual(result["preview"], [{"value": "0"}])

    def test_source_is_immutable_and_missing_values_are_not_filled(self):
        payload = csv_bytes(["id", "value"], [["0001", ""], ["0002", "NA"]])
        before = bytes(payload)
        result = cleaning.preview_table(payload, "fixture.csv", options())
        self.assertEqual(payload, before)
        self.assertEqual([row["value"] for row in result["preview"]], ["", "NA"])

    def test_string_filters_are_literal_not_regex_or_python(self):
        payload = csv_bytes(["id", "text"], [["001", "a.*"], ["002", "abc"], ["003", ""]])
        cases = [("eq", "abc", ["002"]), ("ne", "abc", ["001", "003"]),
                 ("contains", ".*", ["001"]), ("is_empty", "", ["003"]), ("not_empty", "", ["001", "002"])]
        for operator, value, expected in cases:
            result = cleaning.preview_table(payload, "fixture.csv", options(filters=[{"column": "text", "operator": operator, "value": value}]))
            self.assertEqual([row["id"] for row in result["preview"]], expected)

    def test_numeric_filters_exclude_non_numbers_without_mutating_retained_values(self):
        payload = csv_bytes(["id", "value"], [["001", "-1.5"], ["002", "3e1"], ["003", "NaN"], ["004", "<2"]])
        cases = [("gt", "0", ["002"]), ("gte", "30", ["002"]), ("lt", "0", ["001"]), ("lte", "-1.5", ["001"])]
        for operator, value, expected in cases:
            result = cleaning.preview_table(payload, "fixture.csv", options(filters=[{"column": "value", "operator": operator, "value": value}]))
            self.assertEqual([row["id"] for row in result["preview"]], expected)
        self.assertEqual(result["preview"][0]["value"], "-1.5")

    def test_unknown_columns_invalid_numbers_and_out_of_range_rows_fail(self):
        payload = b"a\n1\n2\n"
        cases = [{"columns": [{"source": "missing", "target": "x"}]},
                 {"filters": [{"column": "missing", "operator": "eq", "value": "1"}]},
                 {"filters": [{"column": "a", "operator": "gt", "value": "NaN"}]},
                 {"row_start": 3}, {"row_end": 3}]
        for change in cases:
            with self.subTest(change=change), self.assertRaises(cleaning.CleaningError):
                cleaning.preview_table(payload, "fixture.csv", options(**change))

    def test_invalid_filter_is_not_ignored_for_empty_table(self):
        with self.assertRaises(cleaning.CleaningError):
            cleaning.preview_table(b"a\n", "fixture.csv", options(filters=[{"column": "a", "operator": "gt", "value": "not-number"}]))

    def test_system_conversion_requires_columns_and_explicit_semantics(self):
        headers = cleaning.get_cleaning_schema()["required_columns"]
        payload = system_fixture([valid_system_row()])
        result = cleaning.preview_table(payload, "fixture.csv", json.dumps({"mode": "system"}))
        self.assertFalse(result["system_ready"])
        self.assertEqual(result["missing_required_columns"], [])
        with self.assertRaises(cleaning.CleaningError):
            cleaning.export_table(payload, "fixture.csv", json.dumps({"mode": "system"}))
        exported, _, result = cleaning.export_table(payload, "fixture.csv", json.dumps({"mode": "system", "confirm_system_semantics": True}))
        self.assertTrue(result["system_ready"])
        self.assertEqual(exported_records(exported)[1][0], "0007")

    def test_system_missing_columns_are_reported_not_synthesized(self):
        result = cleaning.preview_table(b"id,lead\n0001,2\n", "fixture.csv", json.dumps({"mode": "system", "confirm_system_semantics": True}))
        self.assertEqual(len(result["missing_required_columns"]), 20)
        self.assertEqual(result["columns"], ["id", "lead"])
        with self.assertRaises(cleaning.CleaningError):
            cleaning.export_table(b"id,lead\n0001,2\n", "fixture.csv", json.dumps({"mode": "system", "confirm_system_semantics": True}))

    def test_custom_output_never_claims_system_ready_even_if_headers_match(self):
        headers = cleaning.get_cleaning_schema()["required_columns"]
        payload = csv_bytes(headers, [["1"] * len(headers)])
        _, _, result = cleaning.export_table(payload, "fixture.csv", options(confirm_system_semantics=True))
        self.assertFalse(result["system_ready"])

    def test_system_empty_result_is_not_ready(self):
        headers = cleaning.get_cleaning_schema()["required_columns"]
        payload = csv_bytes(headers, [])
        result = cleaning.preview_table(payload, "fixture.csv", json.dumps({"mode": "system", "confirm_system_semantics": True}))
        self.assertFalse(result["system_ready"])
        with self.assertRaises(cleaning.CleaningError):
            cleaning.export_table(payload, "fixture.csv", json.dumps({"mode": "system", "confirm_system_semantics": True}))

    def test_download_is_utf8_bom_actual_values_match_preview(self):
        payload = csv_bytes(["姓名", "id"], [["测试", "0001"]])
        exported, name, result = cleaning.export_table(payload, "../input.csv", options())
        self.assertTrue(exported.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(name, "cleaned_input.csv")
        self.assertEqual(dict(zip(exported_records(exported)[0], exported_records(exported)[1])), result["preview"][0])

    def test_formula_injection_is_protected_even_without_trimming(self):
        inputs = ["=1+1", " +SUM(A1)", "\t=1+1", "\r-foo", "@SUM(A1)", "-evil", "-1.25", "+2e3", "NaN", "001"]
        payload = csv_bytes(["value"], [[value] for value in inputs])
        exported, _, result = cleaning.export_table(payload, "fixture.csv", options(trim_text=False))
        actual = [row[0] for row in exported_records(exported)[1:]]
        self.assertEqual(actual[:6], ["'" + value for value in inputs[:6]])
        self.assertEqual(actual[6:], inputs[6:])
        self.assertEqual([row["value"] for row in result["preview"]], actual)
        self.assertEqual(next(entry for entry in result["audit"] if entry["action"] == "csv_formula_protection")["protected_cells"], 6)

    def test_header_formulas_are_protected_and_collisions_rejected(self):
        exported, _, result = cleaning.export_table(b"=1+1,a\nx,y\n", "fixture.csv", options())
        self.assertEqual(exported_records(exported)[0][0], "'=1+1")
        self.assertEqual(result["columns"][0], "'=1+1")
        with self.assertRaises(cleaning.CleaningError):
            cleaning.export_table(b"=1+1,'=1+1\nx,y\n", "fixture.csv", options())

    def test_non_ascii_and_control_whitespace_cannot_bypass_formula_protection(self):
        values = ["\u00a0=1+1", "\v@SUM(A1)", "\ufeff=1+1", "\f-cmd", "\t+2"]
        exported, _, result = cleaning.export_table(csv_bytes(["value"], [[value] for value in values]), "fixture.csv", options(trim_text=False))
        self.assertEqual([row[0] for row in exported_records(exported)[1:]], ["'" + value for value in values])
        self.assertEqual([row["value"] for row in result["preview"]], ["'" + value for value in values])

    def test_xlsx_formulas_are_safe_on_csv_export(self):
        exported, _, result = cleaning.export_table(xlsx_bytes([["id", "formula"], ["001", "=2+2"]]), "fixture.xlsx", options())
        self.assertEqual(exported_records(exported)[1], ["001", "'=2+2"])
        self.assertEqual(result["preview"][0]["formula"], "'=2+2")

    def test_output_buffer_has_a_hard_byte_limit_before_materializing_large_csv(self):
        payload = csv_bytes(["value"], [['"' * 20], ['"' * 20]])
        with patch.object(cleaning, "MAX_OUTPUT_BYTES", 30), self.assertRaises(cleaning.CleaningError):
            cleaning.export_table(payload, "fixture.csv", options())


class SystemRowQualityTests(unittest.TestCase):
    def test_system_rows_are_checked_but_semantics_are_never_auto_confirmed(self):
        payload = system_fixture([valid_system_row(), valid_system_row("0008", DEMO_J__RIDAGEYR="17")])
        result = cleaning.preview_table(payload, "fixture.csv", system_options(confirm_system_semantics=False, drop_invalid_system_rows=True))
        self.assertTrue(result["row_quality"]["checked"])
        self.assertEqual(result["row_quality"]["dropped_rows"], 1)
        self.assertEqual(result["total_rows"], 1)
        self.assertFalse(result["system_ready"])
        with self.assertRaises(cleaning.CleaningError):
            cleaning.export_table(payload, "fixture.csv", system_options(confirm_system_semantics=False, drop_invalid_system_rows=True))

    def test_default_checks_allow_original_missing_descriptive_values_and_third_readings(self):
        row = valid_system_row(BPXO_J__BPXOSY3="", BPXO_J__BPXODI3="", PBCD_J__LBXBPB="", DEMO_J__DMDEDUC2="")
        result = cleaning.preview_table(system_fixture([row]), "fixture.csv", system_options())
        self.assertEqual(result["row_quality"]["valid_rows"], 1)
        self.assertEqual(result["row_quality"]["invalid_rows"], 0)
        self.assertTrue(result["system_ready"])
        self.assertEqual(result["preview"][0]["PBCD_J__LBXBPB"], "")

    def test_identifier_age_numeric_and_blood_pressure_format_errors_are_explicit(self):
        rows = [valid_system_row(""), valid_system_row("2", DEMO_J__RIDAGEYR=""),
                valid_system_row("3", DEMO_J__RIDAGEYR="17"), valid_system_row("4", BPXO_J__BPXOSY3="bad"),
                valid_system_row("5", BPXO_J__BPXODI3="inf"), valid_system_row("6", BPXO_J__BPXODI3="0"),
                valid_system_row("7", PBCD_J__LBXBPB="<0.2"), valid_system_row("8", DEMO_J__RIAGENDR="Male")]
        result = cleaning.preview_table(system_fixture(rows), "fixture.csv", system_options())
        quality = result["row_quality"]
        self.assertEqual((quality["checked_rows"], quality["valid_rows"], quality["invalid_rows"]), (8, 0, 8))
        codes = {reason["code"] for reason in quality["reasons"]}
        self.assertTrue({"identifier_missing", "age_invalid", "age_under_18", "blood_pressure_format_invalid", "numeric_field_invalid"}.issubset(codes))
        self.assertFalse(result["system_ready"])
        self.assertEqual(result["total_rows"], 8)
        self.assertTrue(all(set(item) == {"row_number", "reason_codes"} for item in quality["invalid_preview"]))
        self.assertNotIn("<0.2", json.dumps(quality))

    def test_current_analysis_reading_boundaries_and_adult_rules_match_existing_cohort(self):
        rows = [
            valid_system_row("0001", DEMO_J__RIDAGEYR="18", BPXO_J__BPXOSY1="50", BPXO_J__BPXOSY2="300", BPXO_J__BPXOSY3="", BPXO_J__BPXODI1="30", BPXO_J__BPXODI2="200", BPXO_J__BPXODI3=""),
            valid_system_row("0002", BPXO_J__BPXOSY1="49", BPXO_J__BPXOSY2="301"),
            valid_system_row("0003", BPXO_J__BPXODI1="29", BPXO_J__BPXODI2="201"),
            valid_system_row("0004", BPXO_J__BPXOSY3="9999", BPXO_J__BPXODI3=""),
            valid_system_row("0005", DEMO_J__RIDAGEYR="17"),
            valid_system_row("0006", PBCD_J__LBXBPB="500000"),
        ]
        config = OUTCOME_CONFIGS["blood_pressure"]
        existing = _build_analysis(pd.DataFrame(rows), config, "fixture", "fixture.csv")
        result = cleaning.preview_table(system_fixture(rows), "fixture.csv", system_options())
        self.assertEqual(result["row_quality"]["valid_rows"], existing["metadata"]["analysis_records"])
        self.assertEqual(result["row_quality"]["valid_rows"], 3)
        self.assertEqual([row["row_number"] for row in result["row_quality"]["invalid_preview"]], [2, 3, 5])
        payload, _, cleaned = cleaning.export_table(system_fixture(rows), "fixture.csv", system_options(drop_invalid_system_rows=True))
        self.assertEqual([row[0] for row in exported_records(payload)[1:]], ["0001", "0004", "0006"])
        self.assertEqual(cleaned["preview"][-1]["PBCD_J__LBXBPB"], "500000")
        self.assertTrue(any("这些读数不计入有效次数" in warning for warning in cleaned["warnings"]))

    def test_two_valid_readings_per_type_are_required_but_blank_third_values_are_allowed(self):
        rows = [valid_system_row("1", BPXO_J__BPXOSY2="", BPXO_J__BPXOSY3=""),
                valid_system_row("2", BPXO_J__BPXODI2="", BPXO_J__BPXODI3=""),
                valid_system_row("3", BPXO_J__BPXOSY3="", BPXO_J__BPXODI3="")]
        result = cleaning.preview_table(system_fixture(rows), "fixture.csv", system_options())
        self.assertEqual(result["row_quality"]["valid_rows"], 1)
        codes = {reason["code"] for reason in result["row_quality"]["reasons"]}
        self.assertEqual(codes, {"sbp_insufficient_readings", "dbp_insufficient_readings"})

    def test_complete_case_is_optional_and_does_not_require_all_three_bp_readings(self):
        rows = [valid_system_row("1", PBCD_J__LBXBPB=""), valid_system_row("2", BPXO_J__BPXOSY3="", BPXO_J__BPXODI3="")]
        default = cleaning.preview_table(system_fixture(rows), "fixture.csv", system_options())
        complete = cleaning.preview_table(system_fixture(rows), "fixture.csv", system_options(require_complete_system_rows=True))
        self.assertEqual(default["row_quality"]["valid_rows"], 2)
        self.assertEqual(complete["row_quality"]["valid_rows"], 1)
        self.assertEqual(complete["row_quality"]["reasons"][0]["code"], "complete_case_missing")
        self.assertFalse(complete["system_ready"])
        _, _, result = cleaning.export_table(system_fixture(rows), "fixture.csv", system_options(require_complete_system_rows=True, drop_invalid_system_rows=True))
        self.assertEqual(result["preview"][0]["SEQN"], "2")

    def test_original_row_numbers_survive_range_filter_mapping_and_deletion(self):
        rows = [valid_system_row("0001"), valid_system_row("0002"), valid_system_row(""),
                valid_system_row("0004", DEMO_J__RIDAGEYR="16"), valid_system_row("0005")]
        result = cleaning.preview_table(system_fixture(rows), "fixture.csv", system_options(
            row_start=2, row_end=5, filters=[{"column": "SEQN", "operator": "ne", "value": "0002"}],
            columns=[{"source": column, "target": column} for column in cleaning.get_cleaning_schema()["required_columns"]],
            drop_invalid_system_rows=True))
        self.assertEqual([item["row_number"] for item in result["row_quality"]["invalid_preview"]], [3, 4])
        self.assertEqual(result["preview"][0]["SEQN"], "0005")
        self.assertEqual(result["row_quality"]["remaining_rows"], 1)
        self.assertEqual(result["row_quality"]["dropped_rows"], 2)
        self.assertEqual(sum(item["removed"] for item in result["audit"]), result["original_rows"] - result["total_rows"])

    def test_reason_counts_can_overlap_and_preview_is_bounded_without_raw_phi(self):
        bad = valid_system_row("", DEMO_J__RIDAGEYR="", BPXO_J__BPXOSY1="", BPXO_J__BPXOSY2="", BPXO_J__BPXOSY3="")
        result = cleaning.preview_table(system_fixture([bad] * 25), "fixture.csv", system_options())
        quality = result["row_quality"]
        self.assertEqual(quality["invalid_rows"], 25)
        self.assertEqual(len(quality["invalid_preview"]), 20)
        self.assertTrue(quality["reason_counts_overlap"])
        self.assertGreater(sum(item["count"] for item in quality["reasons"]), quality["invalid_rows"])
        self.assertEqual(quality["invalid_preview"][0]["row_number"], 1)

    def test_missing_column_skips_row_check_and_cannot_be_hidden_by_deleting_rows(self):
        result = cleaning.preview_table(b"id,value\n001,2\n", "fixture.csv", system_options(drop_invalid_system_rows=True))
        quality = result["row_quality"]
        self.assertFalse(quality["checked"])
        self.assertEqual(quality["checked_rows"], 0)
        self.assertEqual(quality["invalid_rows"], 0)
        self.assertEqual(len(quality["column_errors"]), 20)
        self.assertEqual(result["total_rows"], 1)
        self.assertEqual(result["preview"][0], {"id": "001", "value": "2"})
        self.assertFalse(result["system_ready"])

    def test_all_invalid_rows_removed_cannot_create_ready_empty_dataset(self):
        payload = system_fixture([valid_system_row("1", DEMO_J__RIDAGEYR="17")])
        result = cleaning.preview_table(payload, "fixture.csv", system_options(drop_invalid_system_rows=True))
        self.assertEqual(result["total_rows"], 0)
        self.assertEqual(result["row_quality"]["dropped_rows"], 1)
        self.assertFalse(result["system_ready"])
        with self.assertRaises(cleaning.CleaningError):
            cleaning.export_table(payload, "fixture.csv", system_options(drop_invalid_system_rows=True))

    def test_system_quality_options_are_strict_and_system_only(self):
        for changes in ({"drop_invalid_system_rows": True}, {"require_complete_system_rows": True},
                        {"mode": "system", "drop_invalid_system_rows": "true"}):
            with self.subTest(changes=changes), self.assertRaises(cleaning.CleaningError):
                cleaning.parse_options(options(**changes))

    def test_nonfinite_descriptive_fields_fail_but_extreme_finite_values_are_not_deleted(self):
        rows = [valid_system_row("1", PBCD_J__LBXBPB="inf"), valid_system_row("2", PBCD_J__LBXBPB="NaN"),
                valid_system_row("3", PBCD_J__LBXBPB="500000", DEMO_J__RIAGENDR="999")]
        result = cleaning.preview_table(system_fixture(rows), "fixture.csv", system_options(drop_invalid_system_rows=True))
        self.assertEqual(result["row_quality"]["invalid_rows"], 2)
        self.assertEqual(result["preview"][0]["SEQN"], "3")
        self.assertEqual(result["preview"][0]["DEMO_J__RIAGENDR"], "999")
        self.assertTrue(result["system_ready"])

    def test_trim_false_numeric_formula_safety_roundtrips_through_actual_batch_import(self):
        rows = [valid_system_row("0007", PBCD_J__LBXBPB=" +1 ", BPXO_J__BPXOSY1="\n+120"),
                valid_system_row("0008", SMQ_J__SMQ020="\t+1 ", PBCD_J__LBXBCD=" 2 ")]
        headers = cleaning.get_cleaning_schema()["required_columns"] + ["note"]
        source = csv_bytes(headers, [[row[column] for column in headers[:-1]] + ["=1+1"] for row in rows])
        before = bytes(source)
        exported, filename, result = cleaning.export_table(source, "fixture.csv", system_options(trim_text=False))
        self.assertEqual(source, before)
        self.assertTrue(result["system_ready"])
        self.assertEqual(result["preview"][0]["PBCD_J__LBXBPB"], "+1")
        self.assertEqual(result["preview"][0]["BPXO_J__BPXOSY1"], "+120")
        self.assertEqual(result["preview"][1]["SMQ_J__SMQ020"], "+1")
        self.assertEqual(result["preview"][1]["PBCD_J__LBXBCD"], " 2 ")
        self.assertEqual(result["preview"][0]["note"], "'=1+1")
        normalized = next(item for item in result["audit"] if item["action"] == "normalize_system_numeric_for_csv")
        self.assertEqual(normalized["changed_cells"], 3)
        self.assertEqual(normalized["removed"], 0)
        with tempfile.TemporaryDirectory(prefix="cleaning_roundtrip_") as upload_dir, \
                patch.object(data_service, "UPLOAD_DIR", upload_dir), \
                patch.dict(data_service.data_store, {}, clear=True), patch.dict(data_service.analysis_store, {}, clear=True):
            imported = asyncio.run(data_service.import_batch_file(exported, filename))
            stored = data_service.data_store[imported.file_id]
            self.assertEqual(imported.analysis_records, 2)
            self.assertEqual(stored["SEQN"].tolist(), ["0007", "0008"])
            self.assertEqual(float(stored.loc[0, "PBCD_J__LBXBPB"]), 1.0)
            self.assertEqual(float(stored.loc[0, "BPXO_J__BPXOSY1"]), 120.0)
            self.assertEqual(float(stored.loc[1, "SMQ_J__SMQ020"]), 1.0)
            self.assertEqual(stored["note"].tolist(), ["'=1+1", "'=1+1"])

    def test_system_numeric_normalization_does_not_touch_identifier_or_free_text(self):
        row = valid_system_row(" +0007 ", PBCD_J__LBXBPB=" +1 ")
        exported, _, result = cleaning.export_table(system_fixture([row]), "fixture.csv", system_options(trim_text=False))
        self.assertEqual(result["preview"][0]["SEQN"], "' +0007 ")
        self.assertEqual(result["preview"][0]["PBCD_J__LBXBPB"], "+1")
        self.assertEqual(exported_records(exported)[1][0], "' +0007 ")

    def test_default_retains_explicit_nonresponse_and_unknown_codes_with_warnings(self):
        rows = [valid_system_row("1", DEMO_J__DMDEDUC2="7"), valid_system_row("2", DEMO_J__DMDMARTL="99"),
                valid_system_row("3", DEMO_J__RIAGENDR="999"), valid_system_row("4", DEMO_J__DMDEDUC2="8")]
        result = cleaning.preview_table(system_fixture(rows), "fixture.csv", system_options(drop_invalid_system_rows=True))
        quality = result["row_quality"]
        self.assertEqual(quality["invalid_rows"], 0)
        self.assertEqual(quality["dropped_rows"], 0)
        self.assertEqual(quality["nonresponse_rows"], 2)
        self.assertEqual(result["total_rows"], 4)
        self.assertTrue(result["system_ready"])
        self.assertTrue(any("未知有限分类编码" in warning for warning in result["warnings"]))
        self.assertTrue(any("官方明确非回答" in warning for warning in result["warnings"]))
        self.assertEqual(sum(entry["unknown_count"] for entry in quality["category_warnings"]), 2)

    def test_strict_field_complete_mode_excludes_only_field_specific_official_nonresponse(self):
        cases = [("DEMO_J__DMDEDUC2", "7"), ("DEMO_J__DMDEDUC2", "9"),
                 ("DEMO_J__DMDMARTL", "77"), ("DEMO_J__DMDMARTL", "99"),
                 ("SMQ_J__SMQ020", "7"), ("SMQ_J__SMQ020", "9"),
                 ("ALQ_J__ALQ111", "7"), ("ALQ_J__ALQ111", "9")]
        rows = [valid_system_row(str(index), **{column: value}) for index, (column, value) in enumerate(cases, 1)]
        rows.append(valid_system_row("9"))
        result = cleaning.preview_table(system_fixture(rows), "fixture.csv", system_options(require_complete_system_rows=True))
        quality = result["row_quality"]
        self.assertEqual(quality["valid_rows"], 1)
        self.assertEqual(quality["invalid_rows"], 8)
        self.assertFalse(result["system_ready"])
        reason = next(item for item in quality["reasons"] if item["code"] == "explicit_nonresponse_code")
        self.assertEqual(reason["count"], 8)
        self.assertEqual(set(reason["columns"]), {column for column, _ in cases})
        exported, _, cleaned = cleaning.export_table(system_fixture(rows), "fixture.csv", system_options(require_complete_system_rows=True, drop_invalid_system_rows=True))
        self.assertEqual(cleaned["total_rows"], 1)
        self.assertEqual(cleaned["row_quality"]["dropped_rows"], 8)
        self.assertEqual(exported_records(exported)[1][0], "9")

    def test_race_seven_is_legal_and_unknown_codes_are_not_silently_excluded_by_strict_mode(self):
        rows = [valid_system_row("1", DEMO_J__RIDRETH3="7", DEMO_J__INDFMPIR="0"),
                valid_system_row("2", DEMO_J__RIDRETH3="7", DEMO_J__INDFMPIR="5"),
                valid_system_row("3", DEMO_J__RIDRETH3="7", DEMO_J__RIAGENDR="999", DEMO_J__DMDEDUC2="8")]
        result = cleaning.preview_table(system_fixture(rows), "fixture.csv", system_options(require_complete_system_rows=True, drop_invalid_system_rows=True))
        self.assertEqual(result["total_rows"], 3)
        self.assertEqual(result["row_quality"]["invalid_rows"], 0)
        self.assertTrue(result["system_ready"])
        self.assertEqual([row["DEMO_J__RIDRETH3"] for row in result["preview"]], ["7", "7", "7"])
        self.assertFalse(any(entry["column"] == "DEMO_J__RIDRETH3" for entry in result["row_quality"]["category_warnings"]))
        self.assertTrue(any("未知有限分类编码" in warning for warning in result["warnings"]))

    def test_nonresponse_numbers_are_not_global_missing_markers_or_new_clinical_thresholds(self):
        rows = [valid_system_row(str(index), PBCD_J__LBXBPB=value, DEMO_J__INDFMPIR=value, DEMO_J__RIDAGEYR="99")
                for index, value in enumerate(("7", "9", "77", "99"), 1)]
        result = cleaning.preview_table(system_fixture(rows), "fixture.csv", system_options(require_complete_system_rows=True, drop_invalid_system_rows=True))
        self.assertEqual(result["total_rows"], 4)
        self.assertEqual(result["row_quality"]["invalid_rows"], 0)
        self.assertEqual(result["row_quality"]["nonresponse_rows"], 0)
        self.assertTrue(result["system_ready"])

    def test_nonresponse_check_audit_has_counts_but_no_raw_record_values(self):
        source = system_fixture([valid_system_row("private-participant", DEMO_J__DMDEDUC2="7")])
        result = cleaning.preview_table(source, "fixture.csv", system_options(require_complete_system_rows=True))
        audit = next(item for item in result["audit"] if item["action"] == "check_system_rows")
        self.assertTrue(audit["complete_case_required"])
        self.assertEqual(audit["explicit_nonresponse_rows"], 1)
        self.assertEqual(audit["removed"], 0)
        self.assertNotIn("private-participant", json.dumps(result["row_quality"]))
        self.assertNotIn("private-participant", json.dumps(result["audit"]))


class CleaningApiTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict("os.environ", {"RAG_API_KEY": "fixture-key", "RAG_REQUIRE_API_KEY": "true"})
        self.env.start()
        app = FastAPI()
        app.middleware("http")(ApiGuard())
        app.include_router(router)
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer fixture-key"}

    def tearDown(self):
        self.client.close()
        self.env.stop()

    def test_auth_is_inherited_for_schema_inspection_preview_and_download(self):
        self.assertEqual(self.client.get("/api/datainput/cleaning/schema").status_code, 401)
        for endpoint in ("inspect", "preview", "export"):
            response = self.client.post("/api/datainput/cleaning/" + endpoint,
                                        files={"file": ("fixture.csv", b"id\n001\n", "text/csv")}, data={"options": options()})
            self.assertEqual(response.status_code, 401)

    def test_real_schema_inspect_preview_and_export_routes(self):
        prefix = "/api/datainput/cleaning/"
        schema = self.client.get(prefix + "schema", headers=self.headers)
        self.assertEqual(schema.status_code, 200)
        self.assertEqual(len(schema.json()["required_columns"]), 20)
        files = {"file": ("测试.csv", csv_bytes(["id", "value"], [["0001", " 2 "]]), "text/csv")}
        inspected = self.client.post(prefix + "inspect", headers=self.headers, files=files)
        self.assertEqual(inspected.json()["total_rows"], 1)
        self.assertEqual(inspected.headers["cache-control"], "no-store")
        preview = self.client.post(prefix + "preview", headers=self.headers, files=files, data={"options": options()})
        self.assertEqual(preview.status_code, 200)
        exported = self.client.post(prefix + "export", headers=self.headers, files=files, data={"options": options()})
        self.assertEqual(exported.status_code, 200)
        self.assertTrue(exported.content.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(exported.headers["x-cleaning-system-ready"], "false")
        self.assertEqual(exported.headers["x-cleaning-row-count"], "1")
        self.assertIn("filename*=UTF-8''", exported.headers["content-disposition"])
        self.assertEqual(exported.headers["cache-control"], "no-store")

    def test_api_errors_are_422_or_413_not_internal_failure_or_data_echo(self):
        prefix = "/api/datainput/cleaning/"
        files = {"file": ("fixture.csv", b"id\n001\n", "text/csv")}
        invalid = self.client.post(prefix + "preview", headers=self.headers, files=files, data={"options": "{"})
        self.assertEqual(invalid.status_code, 422)
        missing = self.client.post(prefix + "export", headers=self.headers, files=files, data={"options": "{}"})
        self.assertEqual(missing.status_code, 422)
        self.assertEqual(self.client.get(prefix + "schema?outcome_id=bad", headers=self.headers).status_code, 422)
        with patch("app.api.data_cleaning.MAX_FILE_BYTES", 1):
            too_large = self.client.post(prefix + "inspect", headers=self.headers, files=files)
        self.assertEqual(too_large.status_code, 413)
        self.assertNotIn("001", invalid.text)

    def test_main_application_registers_cleaning_router(self):
        from app.main import app
        paths = {route.path for route in app.routes}
        self.assertIn("/api/datainput/cleaning/schema", paths)
        self.assertIn("/api/datainput/cleaning/export", paths)


if __name__ == "__main__":
    unittest.main()
