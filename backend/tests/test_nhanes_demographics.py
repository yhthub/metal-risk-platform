"""Real raw-file denominators without inference, fitting or external IO."""
import json
import unittest

import numpy as np
import pandas as pd

from app.services.nhanes_demographic_service import demographic_profile


class DemographicProfileTests(unittest.TestCase):
    def test_all_raw_rows_and_unknowns_close_independent_of_model_eligibility(self):
        source = pd.DataFrame({
            "DEMO_J__RIAGENDR": [1, 2, 1, 9, np.nan, 2],
            "DEMO_J__RIDAGEYR": [17, 18, 40, 80, 81, np.nan],
            "BMX_J__BMXBMI": [22, 0, np.nan, -1, 30, 40],
            "DEMO_J__DMDMARTL": [1, 2, 3, 4, 5, 6],
            "DEMO_J__DMDEDUC2": [1, 2, 3, 4, 5, 9],
            "PBCD_J__LBXBPB": [np.nan] * 6,
        })
        original = source.copy(deep=True)
        profile = demographic_profile(source)
        pd.testing.assert_frame_equal(source, original)
        self.assertEqual(profile["total_records"], 6)
        self.assertEqual(profile["scope"], "all_uploaded_records")
        self.assertFalse(profile["weighted"])
        for name in ("sex", "marital", "education", "smoking"):
            distribution = profile[name]
            self.assertEqual(sum(item["count"] for item in distribution["categories"]), 6)
            self.assertAlmostEqual(sum(item["percent"] for item in distribution["categories"]), 100)
            self.assertEqual(distribution["valid_count"] + distribution["unknown_count"], 6)
            self.assertLessEqual(distribution["missing_count"], distribution["unknown_count"])
        sexes = {item["key"]: item for item in profile["sex"]["categories"]}
        self.assertEqual([sexes[key]["count"] for key in ("male", "female", "unknown")], [2, 2, 2])
        self.assertEqual(profile["sex"]["missing_count"], 1)
        self.assertEqual(profile["age"]["valid_count"], 4)
        self.assertEqual(profile["age"]["missing_count"], 1)
        self.assertEqual(profile["age"]["invalid_count"], 1)
        self.assertEqual(profile["age"]["mean"], (17 + 18 + 40 + 80) / 4)
        self.assertEqual(profile["age"]["min"], 17)
        self.assertEqual(sum(item["count"] for item in profile["age"]["bands"]), 6)
        self.assertEqual([item["count"] for item in profile["age"]["bands"]], [1, 1, 1, 1, 2])
        self.assertEqual(profile["bmi"]["valid_count"], 3)
        self.assertEqual(profile["bmi"]["invalid_count"], 2)
        self.assertAlmostEqual(profile["bmi"]["mean"], 92 / 3)
        json.dumps(profile, allow_nan=False)

    def test_absent_optional_columns_are_explicit_unknown_not_invented_categories(self):
        profile = demographic_profile(pd.DataFrame({"SEQN": [1, 2, 3]}))
        for name in ("sex", "marital", "education", "smoking"):
            self.assertFalse(profile[name]["available"])
            self.assertEqual(profile[name]["missing_count"], 3)
            self.assertEqual(profile[name]["unknown_count"], 3)
            self.assertTrue(all(item["count"] == (3 if item["key"] == "unknown" else 0)
                                for item in profile[name]["categories"]))
        for name in ("age", "bmi"):
            self.assertFalse(profile[name]["available"])
            self.assertIsNone(profile[name]["mean"])
            self.assertIsNone(profile[name]["median"])
            self.assertIsNone(profile[name]["min"])
            self.assertIsNone(profile[name]["max"])
            self.assertEqual(profile[name]["valid_count"], 0)

    def test_refused_dont_know_noninteger_and_mislabeled_strings_are_not_recoded(self):
        source = pd.DataFrame({"DEMO_J__RIAGENDR": ["male", "female", True, 1.1, "", 1],
                               "DEMO_J__DMDMARTL": [77, 99, 7, 9, np.nan, "married"],
                               "DEMO_J__DMDEDUC2": [7, 9, 3.5, np.inf, "bachelor", None],
                               "DEMO_J__RIDAGEYR": [25.5, -1, np.inf, "adult", "", 80]})
        result = demographic_profile(source)
        self.assertEqual(result["sex"]["valid_count"], 1)
        self.assertEqual(result["marital"]["unknown_count"], 6)
        self.assertEqual(result["education"]["unknown_count"], 6)
        self.assertEqual(result["age"]["valid_count"], 1)
        self.assertEqual(result["age"]["mean"], 80)
        json.dumps(result, allow_nan=False)

    def test_smoking_uses_exact_lifetime_and_current_frequency_not_drinking(self):
        source = pd.DataFrame({"SMQ_J__SMQ020": [2, 1, 1, 1, 1, 7, None],
                               "SMQ_J__SMQ040": [np.nan, 1, 2, 3, np.nan, 3, 1],
                               "ALQ_J__ALQ111": [1] * 7})
        result = demographic_profile(source)
        smoking = result["smoking"]
        self.assertEqual([item["count"] for item in smoking["categories"]], [1, 1, 2, 3])
        self.assertEqual(smoking["missing_count"], 2)
        self.assertNotIn("alcohol_any_past_year", result)

    def test_zero_records_leave_no_numeric_estimate_and_finite_percent(self):
        result = demographic_profile(pd.DataFrame())
        self.assertEqual(result["total_records"], 0)
        self.assertIsNone(result["age"]["mean"])
        self.assertTrue(all(item["percent"] == 0 for item in result["sex"]["categories"]))
        json.dumps(result, allow_nan=False)

    def test_finite_source_numbers_do_not_overflow_numeric_median(self):
        result = demographic_profile(pd.DataFrame({"BMX_J__BMXBMI": [1e308, 1e308]}))
        self.assertEqual(result["bmi"]["mean"], 1e308)
        self.assertEqual(result["bmi"]["median"], 1e308)
        json.dumps(result, allow_nan=False)

    def test_final_record_after_old_500_cap_is_included_in_raw_demographics(self):
        source = pd.DataFrame({"DEMO_J__RIAGENDR": [1] * 600 + [2],
                               "DEMO_J__RIDAGEYR": [25] * 600 + [80],
                               "DEMO_J__DMDEDUC2": [3] * 600 + [5]})
        result = demographic_profile(source)
        self.assertEqual(result["total_records"], 601)
        self.assertEqual(result["sex"]["categories"][1]["count"], 1)
        self.assertEqual(result["age"]["max"], 80)
        self.assertEqual(result["education"]["categories"][4]["count"], 1)


if __name__ == "__main__":
    unittest.main()
