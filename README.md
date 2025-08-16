# ODIS project explorer

This Python project is meant to unpack (and make use of) the data stored in MCD Runtime Projects ([colloquially known as "*.db and .key files*"](http://nefariousmotorsports.com/forum/index.php?topic=10318.msg108305#msg108305)).

Normally, these files are used by the MCD Kernel which is then used by ODIS or iDEX or whatever.
Provided with every ODIS installation is an app `MCD-Kernel/VWMCDClient.exe` which can be used to mess around with the projects at a much lower level.

To use this data, one would normally use the libraries from `Include_Libs` and `MCD-Kernel` to write their own C++/Java app that parses the objects.
There are a few issues with this approach, though:
  1. You have to either figure out how to calculate the "secret MAC" to unlock the kernel for use, or crack the .dll.
  2. Almost every function call must be guarded, as exceptions are thrown when the requested element is not defined.
  3. Some database elements are not directly accessible using the provided API, or at least hard to reach.

With this tool, you can approach the databases from the lowest level possible.
I hope it is useful for the study of ODX, J2534, UDS and whatever else.

## A bit of info

> [!NOTE]
> No projects/databases will ever be provided!
> Please bring your own :)

The way these projects work, is that the pairs of .db and .key files represent "Pools" (and "PoolID" refers to the filename without extension).
Each pool contains Objects.

Any object is stored as a data stream, whose bytes will be read as flags/strings/numbers etc.
Every one is stored differently, so... a lot of time was poured into Ghidra and x64dbg.
You can probably appreciate the work it took by taking a look inside the `object_loaders` folder.

Under no circumstances do I guarantee that I am loading every object type correctly.
On the contrary, many fields were named as what I felt they represented.
Basically every class in the C++ library inherits from other classes and I have to admit I couldn't really wrap my head around it when decompiled.

## Getting started

For text translation, HSQLDB is needed, which can only be used through Java.
Therefore, JPype will need to be installed:
```python
pip install jpype1
```

For usage info of each script, call them with argument '**-h**' (or just look at the source code).

The scripts which have the option of text translation (`dumpDTC` and `parseMWB`) will need a database.
  - Take a look in your ODIS data folder (somewhere around `C:/ProgramData`), there should be a `DIDB/db` folder.
  - It must contain a .data file with name `didb_Base-...`, where '...' is a language like 'en_US'.
  - So, provide the scripts with that folder's path and the language suffix.

If you do not provide such a database, for `dumpDTC` you will not have the "more detailed description",
and for `parseMWB` everything will use its default LONG-NAME from ODX.

## Script info

### `dumpProject` / `dumpAllProjects`

These modules will dump every Object from every Pool (from every Project).
Be advised that dumping all projects will require a few tens of gigabytes and take a couple of hours.
I personally worked with a separate partition that I could format to quickly delete all files.

In the current state, all my projects get dumped without errors.
I tried projects from 2020 and 2022.
It's possible that older/newer projects will fail to dump for various reasons, most likely unhandled object types,
or unhandled fields in handled object types (which I hardcoded since they were the same in all projects).

> [!TIP]
> ```powershell
> python dumpProject.py "C:/ProgramData/OE/MCD-Projects-E/VWMCD/AU21X" "O:/Projects"
> ```
> ```powershell
> python dumpAllProjects.py "C:/ProgramData/OE/MCD-Projects-E/VWMCD" "O:/Projects"
> ```

### `dumpECUVariantPatterns`

This script will dump "ECU-VARIANT matching patterns", necessary for the "variant identification" procedure (selecting the appropriate file for an ECU).

> [!TIP]
> ```powershell
> python dumpECUVariantPatterns.py basevariant "C:/ProgramData/OE/MCD-Projects-E/VWMCD/AU21X" "0.0.0@BV_DashBoardUDS.bv" "O:/Patterns"
> ```
> ```powershell
> python dumpECUVariantPatterns.py project "C:/ProgramData/OE/MCD-Projects-E/VWMCD/AU21X" "O:/Patterns"
> ```
> ```powershell
> python dumpECUVariantPatterns.py projects "C:/ProgramData/OE/MCD-Projects-E/VWMCD" "O:/Patterns"
> ```

### `dumpDTC`

This script will dump "DTC definitions".
It will only dump the objects necessary for DTCs (= diagnostic trouble codes) - service 0x19.

> [!TIP]
> ```powershell
> python dumpDTC.py basevariant "C:/ProgramData/OE/MCD-Projects-E/VWMCD/AU21X" "0.0.0@BV_DashBoardUDS.bv" "O:/DTCs" "C:/ProgramData/OE/DIDB/db" en_US
> ```
> ```powershell
> python dumpDTC.py project "C:/ProgramData/OE/MCD-Projects-E/VWMCD/AU21X" "O:/DTCs" "C:/ProgramData/OE/DIDB/db" en_US
> ```
> ```powershell
> python dumpDTC.py projects "C:/ProgramData/OE/MCD-Projects-E/VWMCD" "O:/DTCs" "C:/ProgramData/OE/DIDB/db" en_US
> ```

### `dumpFreezeFrames`

This script will dump "Freeze Frame definitions".
It will only dump the objects necessary for DTC extended data records - service 0x19, mode 0x06.

> [!TIP]
> ```powershell
> python dumpFreezeFrames.py basevariant "C:/ProgramData/OE/MCD-Projects-E/VWMCD/AU21X" "0.0.0@BV_DashBoardUDS.bv" "O:/FFs" "C:/ProgramData/OE/DIDB/db" en_US
> ```
> ```powershell
> python dumpFreezeFrames.py project "C:/ProgramData/OE/MCD-Projects-E/VWMCD/AU21X" "O:/FFs" "C:/ProgramData/OE/DIDB/db" en_US
> ```
> ```powershell
> python dumpFreezeFrames.py projects "C:/ProgramData/OE/MCD-Projects-E/VWMCD" "O:/FFs" "C:/ProgramData/OE/DIDB/db" en_US
> ```

### `dumpAdaptations`

This script will dump "Adaptation definitions".
It will only dump the objects necessary for Calibration Data Writing (= values you can change in the ECU) - service 0x2E.

> [!TIP]
> ```powershell
> python dumpAdaptations.py basevariant "C:/ProgramData/OE/MCD-Projects-E/VWMCD/AU21X" "0.0.0@BV_DashBoardUDS.bv" "O:/ADPs"
> ```
> ```powershell
> python dumpAdaptations.py project "C:/ProgramData/OE/MCD-Projects-E/VWMCD/AU21X" "O:/ADPs"
> ```
> ```powershell
> python dumpAdaptations.py projects "C:/ProgramData/OE/MCD-Projects-E/VWMCD" "O:/ADPs"
> ```

### `dumpCoding`

This script will dump "Coding definitions".
It will only dump the objects necessary for Variant Coding - service 0x2E, DID 0x0600.

> [!TIP]
> ```powershell
> python dumpCoding.py basevariant "C:/ProgramData/OE/MCD-Projects-E/VWMCD/AU21X" "0.0.0@BV_DashBoardUDS.bv" "O:/VRCs"
> ```
> ```powershell
> python dumpCoding.py project "C:/ProgramData/OE/MCD-Projects-E/VWMCD/AU21X" "O:/VRCs"
> ```
> ```powershell
> python dumpCoding.py projects "C:/ProgramData/OE/MCD-Projects-E/VWMCD" "O:/VRCs"
> ```

### `dumpMWB`

This script will dump "MWB definitions".
It will only dump the objects necessary for MWBs (= Messwertblöcke - Measuring blocks) - service 0x22.

This is by far the most important and non-standardized part of UDS diagnostics, one of the main purposes of this project.

> [!TIP]
> ```powershell
> python dumpMWB.py basevariant "C:/ProgramData/OE/MCD-Projects-E/VWMCD/AU21X" "0.0.0@BV_DashBoardUDS.bv" "O:/MWBs"
> ```
> ```powershell
> python dumpMWB.py project "C:/ProgramData/OE/MCD-Projects-E/VWMCD/AU21X" "O:/MWBs"
> ```
> ```powershell
> python dumpMWB.py projects "C:/ProgramData/OE/MCD-Projects-E/VWMCD" "O:/MWBs"
> ```

### `parseMWB`

This script will take a UDS service 0x22 response and parse it similarly to the MCD Kernel.
It probably took the most amount of work, apart from the object loaders.

> [!TIP]
> ```powershell
> python parseMWB.py "C:/ProgramData/OE/MCD-Projects-E/VWMCD/AU21X" "0.0.0@BV_EnginContrModul1UDS.bv" "EV_ECM25TFS0118U0907404C_001" 0xF40C C0E4 "C:/ProgramData/OE/DIDB/db" en_US
> ```

A few more examples are provided in `docs/mwb_examples.txt`.

### `dumpHSQLDB`

This script will dump the contents of all tables of an HSQLDB database.
The username and password are hardcoded, but I don't expect them to ever change.
If you encounter problems, check out the [following chapter](#hsqldb).

> [!TIP]
> ```powershell
> python dumpHSQLDB.py "C:/ProgramData/OE/DIDB/db" "didb_Base-en_US" "O:\HSQLDB"
> ```

## HSQLDB

The included `bin/hsqldb.jar` is an unmodified release from SourceForge, version 1.8.0.

If you encounter issues like "user does not exist" when providing a translation database,
you can rename `hsqldb.jar` to something else and rename `hsqldb_mod.jar` to `hsqldb.jar`.
That one has been modified to automatically dump all users and passwords of a database at startup.

> [!NOTE]
> The "user does not exist" error may also be shown if the database was somehow loaded incorrectly.
> Please ensure you provided the correct path.

The modified .jar will write something like this to the standard output:
```
Name: PUBLIC, password: null
Name: _SYSTEM, password: null
Name: SA, password: ENMGZIRN
Name: VAUDASISTSUPER, password: ENMGZIRN
```

As a side effect, this will always be printed when HSQLDB is used from one of the scripts that need it.

> [!TIP]
> If you wish to start a server from a database (for your own experiments), run this from inside the `bin` folder:
> ```powershell
> java -cp hsqldb.jar org.hsqldb.Server -database.0 file:"C:/ProgramData/OE/DIDB/db/didb_Base-en_US" -dbname.0 testdb
> ```
> You will connect to it using the URL `jdbc:hsqldb:hsql://localhost/testdb`.

## Contributing

If anyone else is dedicated/bored enough, they are very welcome to contribute to this project, even just submitting an issue.

If you want to add functionality (like dumping other important stuff), you are free to take a look how things are dumped currently,
like MWBs or DTCs, then use `dumpProject` and search around with a text editor for object names, fields and such.

## Extra info

In `docs/MCD-2D.md` you can find the documentation used for the validation of data, nicely formatted.

The included `bin/pbl.dll` is simply compiled from the PBL library by Mission-Base.
It is necessary for accessing the .key files.

---

No AI was harmed in the making of this waste of resources. Just a bit of help for the `LongNameTranslation` module. I couldn't be arsed to figure out Java and SQL integration myself.
