#!/usr/bin/env python3
"""Print the headless QEMU arguments for an existing vphone machine bundle."""

import argparse
import json
import plistlib
from pathlib import Path


def boot_arguments(bundle, memory_mib, cpus):
    config = plistlib.loads((bundle / "config.plist").read_bytes())
    if config["platformType"] != "vresearch101":
        raise ValueError("expected a vresearch101 machine")

    def member(name):
        if Path(name).name != name or "," in str(bundle / name):
            raise ValueError(f"unsupported bundle path: {name}")
        path = bundle / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing or linked bundle file: {name}")
        return path

    roms = config["romImages"]
    boot_rom = member(roms["avpBooter"])
    sep_rom = member(roms["avpSEPBooter"])
    disk = member(config["diskImage"])
    nvram = member(config["nvramStorage"])
    sep_storage = member(config["sepStorage"])
    ecid = plistlib.loads(config["machineIdentifier"])["ECID"]
    machine = f"vresearch101,ecid={ecid:x},sep-rom={sep_rom}"
    return [
        "-machine", machine,
        "-accel", "tcg,tb-size=128",
        "-smp", f"{cpus},maxcpus={cpus + 1}",
        "-m", str(memory_mib),
        "-bios", str(boot_rom),
        "-drive", f"file={nvram},if=pflash,format=raw,offset=16384,file.locking=off",
        "-drive", f"file={disk},if=pflash,format=raw,file.locking=off",
        "-drive", f"file={disk},if=none,id=root-pci,format=raw,file.locking=off",
        "-drive", f"file={nvram},if=none,id=aux-pci,format=raw,offset=16384,file.locking=off",
        "-drive", f"file={sep_storage},if=none,id=sep-storage,format=raw,file.locking=off",
        "-display", "none",
        "-serial", "stdio",
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--memory-mib", type=int, default=3072)
    parser.add_argument("--cpus", type=int, default=2)
    args = parser.parse_args()
    if args.memory_mib < 1 or args.cpus < 1:
        parser.error("memory and CPU count must be positive")
    try:
        arguments = boot_arguments(args.bundle.resolve(), args.memory_mib, args.cpus)
    except (OSError, ValueError, TypeError, KeyError, plistlib.InvalidFileException) as error:
        parser.error(str(error))
    print(json.dumps(arguments, indent=2))


if __name__ == "__main__":
    main()
