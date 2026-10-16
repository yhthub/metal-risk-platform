"""Offline restore-unit contracts; no restore, secrets, SSH or model requests.

These checks do not prove systemd's device/IO controls work on the target host,
or that an already running API gates consumption on the final PASS receipt.
"""
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
UNIT = (ROOT / "deploy/aliyun-corpus-restore.service").read_text(encoding="utf-8")
SCRIPT = (ROOT / "scripts/aliyun_restore_closed_corpus.py").read_text(encoding="utf-8")


def values(key):
    return re.findall(r"^" + re.escape(key) + r"=(.*)$", UNIT, re.MULTILINE)


def test_restore_is_one_bounded_run_not_enabled_or_restarted():
    assert values("Type") == ["oneshot"]
    assert values("Restart") == ["no"]
    assert values("RemainAfterExit") == ["yes"]
    assert values("TimeoutStartSec") == ["8h"]
    assert values("TimeoutStopSec") == ["30s"]
    assert "[Install]" not in UNIT
    assert not values("WantedBy")
    assert not values("ExecReload")
    assert not values("OnCalendar")
    assert not values("OnUnitActiveSec")


def test_restore_has_fixed_private_interpreter_release_and_mount_scope():
    assert values("RequiresMountsFor") == ["/data/zhiwei"]
    assert values("User") == values("Group") == ["root"]
    assert values("WorkingDirectory") == ["/data/zhiwei/releases/site_20261011_001/scripts"]
    assert values("ExecStart") == [
        "/data/zhiwei/runtime/venv/bin/python "
        "/data/zhiwei/releases/site_20261011_001/scripts/aliyun_restore_closed_corpus.py --wait 21600"
    ]
    assert not values("EnvironmentFile")
    assert "RAG_API_KEY=" not in UNIT and "RAG_LLM_API_KEY=" not in UNIT


def test_restore_only_writes_new_corpus_and_preserves_source_and_existing_site():
    assert values("ProtectSystem") == ["strict"]
    assert values("ReadWritePaths") == ["/data/zhiwei/corpus"]
    assert values("ReadOnlyPaths") == [
        "/data/zhiwei/corpus/transfer /data/zhiwei/private /data/zhiwei/runtime /data/zhiwei/releases"
    ]
    assert values("UMask") == ["0077"]
    commands = "\n".join(values("ExecStart") + values("ExecStartPre") + values("ExecStop"))
    for forbidden in ("/etc/nginx", "/www/server", "systemctl", "docker", "mkfs", "apt ", " mount "):
        assert forbidden not in commands


def test_restore_has_no_network_or_privilege_expansion():
    for key in ("NoNewPrivileges", "PrivateTmp", "PrivateDevices", "PrivateNetwork", "ProtectHome",
                "ProtectKernelTunables", "ProtectKernelModules", "ProtectControlGroups",
                "RestrictSUIDSGID", "LockPersonality"):
        assert values(key) == ["true"]
    assert values("RestrictAddressFamilies") == ["AF_UNIX"]
    assert values("SystemCallArchitectures") == ["native"]
    assert values("CapabilityBoundingSet") == [""]


def test_restore_low_memory_cpu_io_and_task_budgets_are_explicit():
    assert values("MemoryMax") == ["256M"]
    assert values("MemorySwapMax") == ["0"]
    assert values("CPUQuota") == ["50%"]
    assert values("IOSchedulingClass") == ["idle"]
    assert values("IOReadBandwidthMax") == ["/dev/nvme1n1 40M"]
    assert values("IOWriteBandwidthMax") == ["/dev/nvme1n1 20M"]
    assert values("TasksMax") == ["8"]
    assert values("LimitNOFILE") == ["128"]


def test_script_checks_exact_ext4_identity_and_schema_before_exclusive_publication():
    # Text only: importing or running the restoration CLI is unnecessary here.
    assert 'DATA_UUID = "25986262-9cf2-4d7b-a42f-40861c30ac5d"' in SCRIPT
    assert 'fields != [DATA_UUID, "ext4", str(root)]' in SCRIPT
    assert 'MAX_WAIT_SECONDS = 21600' in SCRIPT
    assert 'with paths.receipt.open("x", encoding="utf-8")' in SCRIPT
    assert 'with partial.open("xb")' in SCRIPT
    assert 'staged_schema = partial_schema_checker(partial)' in SCRIPT
    assert SCRIPT.index('staged_schema = partial_schema_checker(partial)') < SCRIPT.index('os.link(partial, target)')
    assert 'os.link(partial, target)' in SCRIPT  # cannot overwrite an existing final
    assert 'published_unverified=published' in SCRIPT  # failures are not disguised as PASS
