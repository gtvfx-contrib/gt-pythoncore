# gt-pythoncore

A collection of pure-Python utilities for the `gt` toolset. No host application
dependencies (Maya, 3ds Max, Houdini, etc.) — only Python and the packages listed
in `requirements.txt`.

---

## Requirements

- **Python 3.9+**
- **Windows** — several modules (`gt.win32`, `gt.winreg`, `gt.winmessages`,
  UNC path helpers) depend on Win32 APIs and will not run on other platforms.
  Pure-utility modules (`gt.pycore`, `gt.config`, `gt.xmlutils`, etc.) are
  platform-agnostic.

---

## Installation

### 1. Install dependencies

From the repo root:

```
pip install -r requirements.txt
```

### 2. Register as an Envoy bundle (recommended)

This repo ships with a pre-configured [`envoy_env/`](envoy_env/) directory, making
it a first-class [Envoy](../envoy/README.md) bundle. The simplest way to make its
packages available is to include this repo in your `ENVOY_BNDL_ROOTS`:

```powershell
# PowerShell — add to your profile for persistence
$env:ENVOY_BNDL_ROOTS = "R:/repo/gtvfx-contrib;R:/repo/gtvfx"
```

Envoy will discover the bundle, load [`envoy_env/python_env.json`](envoy_env/python_env.json)
(which appends `py/` to `PYTHONPATH`), and register any commands defined in
[`envoy_env/commands.json`](envoy_env/commands.json) — including `branch_status`.

See the [Envoy README](../envoy/README.md) for full setup details.

### Alternative: manual path configuration

If you are not using Envoy, add `py/` to your Python path directly:

```python
import sys
sys.path.insert(0, r"path\to\gt\pythoncore\py")
```

Or via environment variable, `.pth` file, or your preferred environment manager:

```powershell
$env:PYTHONPATH = "R:/repo/gtvfx-contrib/gt/pythoncore/py;$env:PYTHONPATH"
```

---

## Package Overview

```
gt/
├── config/         INI / config file parsing
├── gitutils/       Git repository helpers
├── logging/        Log-level helpers and decorators
├── metaclasses/    Singleton metaclasses
├── pycore/         Core path, filesystem, string, and system utilities
├── repl/           Interactive REPL / terminal utilities
├── rest/           Base class for REST API clients
├── win32/          Win32 file version helpers
├── winmessages/    Win32 message-box wrapper
├── winreg/         Windows Registry read/write helpers
└── xmlutils/       ElementTree XML helpers
```

---

## Modules

### `gt.config`

INI-style config file helpers with automatic encoding detection.

| Symbol | Description |
|---|---|
| `ConfigParser` | `configparser.ConfigParser` subclass with `chardet`-based encoding detection |
| `detectEncoding` | Detect the character encoding of a file |

---

### `gt.gitutils`

High-level wrappers around [GitPython](https://gitpython.readthedocs.io/).

| Symbol | Description |
|---|---|
| `repoRoot` | Return the root path of the repo containing a given path |
| `getLocalRepos` | Discover all git repos under a search root |
| `findRepoByBranchName` | Find a local repo that has a branch matching a name |
| `getCurrentBranchName` | Return the active branch name for a repo |
| `getUnstagedFiles` | List files with unstaged changes |
| `add` | Stage files |
| `commit` | Create a commit |
| `push` | Push commits to remote |
| `pull` | Pull from remote |
| `checkout` | Checkout a branch |

**CLI tool** — `gt.gitutils.tools.branch_status` provides a Click-based command
for reporting branch status across multiple local repos.

---

### `gt.logging`

| Symbol | Description |
|---|---|
| `setLevel` | Configure the log level for any named logger |
| `logFunc` | Decorator that logs entry/exit of a function |

---

### `gt.metaclasses`

| Symbol | Description |
|---|---|
| `Singleton` | Thread-safe singleton metaclass |
| `ABCSingleton` | Singleton metaclass compatible with `ABCMeta` |

```python
class MyService(metaclass=Singleton):
    ...
```

---

### `gt.pycore`

The largest module. All symbols are re-exported from the `gt.pycore` namespace.

#### Constants

| Symbol | Description |
|---|---|
| `LOCAL_ROOT` | Platform-appropriate local app-data root (via `platformdirs`) |
| `NET_STORAGE_MAP` | UNC-to-drive-letter mapping parsed from `NET_STORAGE_MAP` env var (JSON) |

Set `NET_STORAGE_MAP` to a JSON object to configure static UNC mappings:

```
NET_STORAGE_MAP={"\\\\server\\share": "S:"}
```

#### Path functions

| Symbol | Description |
|---|---|
| `ensurePath` | Create a directory (or the parent of a file path) if it doesn't exist |
| `extendedCharacterPath` | Prepend `\\?\` for paths that exceed MAX_PATH |
| `makeRelativePath` | Return a path relative to a given base |
| `makeLegalDirectoryName` | Strip characters illegal in directory names |
| `explorePath` | Open a path in Windows Explorer |
| `initializeNetworkShare` | Verify a UNC share is accessible |
| `netFileExists` | Check file existence on a UNC path |
| `getActiveDriveMappings` | Return all current drive-letter → UNC mappings via `WNetGetConnectionW` |
| `uncToMappedDrive` | Translate a UNC path to its mapped drive-letter equivalent |
| `copytreeWithProgress` | `shutil.copytree` with a `tqdm` progress bar |

#### Filesystem functions

| Symbol | Description |
|---|---|
| `robocopy` | Python wrapper around Windows `robocopy` |
| `rmdir` | Recursively remove a directory tree |
| `pruneDirectories` | Delete empty directories under a root |

#### Archive functions

| Symbol | Description |
|---|---|
| `compressFiles` | Create a 7-Zip archive from a list of paths |
| `extractArchive` | Extract a 7-Zip archive to a destination |

Requires 7-Zip to be on `PATH` or installed at the default location.

#### Context managers

| Symbol | Description |
|---|---|
| `managedOutput` | Redirect or suppress stdout/stderr |
| `mappedDrive` | Temporarily map a UNC path to a drive letter via `net use` |
| `retryContext` | Retry a block of code on exception with configurable back-off |

```python
from gt.pycore import mappedDrive

with mappedDrive(r"\\server\share") as drive:
    print(drive)  # e.g. "Z:"
```

#### Decorators

| Symbol | Description |
|---|---|
| `conformPath` | Normalize path separators on decorated function arguments |
| `normalizePaths` | Resolve and absolutize path arguments |
| `PathStyle` | Enum controlling path normalization style |
| `timeIt` | Log the execution time of a function |

#### String functions

| Symbol | Description |
|---|---|
| `isMatch` | Glob/wildcard matching |
| `formatDataSize` | Human-readable byte size (KB, MB, GB…) |
| `formatTime` | Human-readable duration from seconds |
| `formatCommandString` | Quote and join a command list for display |
| `verPadding` | Zero-pad version string components |
| `getTimecodeVersion` | Build a version string from a timestamp |

#### System functions

| Symbol | Description |
|---|---|
| `findExecutable` | Locate an executable by name (`shutil.which` + `where` fallback) |
| `getNumCores` | Return the logical CPU core count |

#### User functions

| Symbol | Description |
|---|---|
| `getUserInfo` | Return Win32 user-info dict for the current or a named user |
| `getUserRealName` | Return the display name for the current or a named user |

#### User paths

| Symbol | Description |
|---|---|
| `userConfigPathLocal` | Per-user local config directory |
| `userDataPathLocal` | Per-user local data directory |
| `userLogPathLocal` | Per-user local log directory |

#### Subprocess helpers

| Symbol | Description |
|---|---|
| `processSubprocessOutput` | Stream and log stdout/stderr from a `subprocess.Popen` object |

---

### `gt.repl`

Utilities for interactive terminal / REPL sessions.

| Symbol | Description |
|---|---|
| `ReplProgress` | Colored progress-bar display using `colorama` |
| `changeWorkingDir` | Context manager that temporarily changes `os.getcwd()` |
| `cmdProgress` | Display a spinner while a callable runs in a thread |
| `waitCursor` | Context manager that shows a terminal wait indicator |

---

### `gt.rest`

Base classes for building REST API clients.

| Symbol | Description |
|---|---|
| `BaseInterface` | Abstract singleton base class; wraps `requests` with auth, retries, and error handling |
| `RestException` | Exception raised on non-2xx responses |
| `CaptureException` | Context manager / decorator that catches and logs `requests` exceptions |

```python
from gt.rest import BaseInterface

class MyApi(BaseInterface):
    BASE_URL = "https://api.example.com"

    def get_items(self):
        return self.get("/items")
```

---

### `gt.win32`

| Symbol | Description |
|---|---|
| `FileVersion` | Dataclass holding `major`, `minor`, `patch`, `build` version components |
| `getFileVersion` | Read the `FileVersion` from a PE binary via `win32api` |

---

### `gt.winmessages`

| Symbol | Description |
|---|---|
| `winMessageBox` | Display a Win32 `MessageBox` dialog from Python |

---

### `gt.winreg`

Full read/write access to the Windows Registry.

| Symbol | Description |
|---|---|
| `getRegistryValue` | Read a single registry value |
| `getRegistryValues` | Read all values in a key |
| `getRegistryValuesDetailed` | Read values with type information |
| `getRegistrySubkeys` | List subkey names |
| `getRegistryKeyInfo` | Return metadata about a key |
| `registryKeyExists` | Check whether a key exists |
| `setRegistryValue` | Write a value (auto-detect type) |
| `setRegistryValueString` | Write a `REG_SZ` value |
| `setRegistryValueDWord` | Write a `REG_DWORD` value |
| `deleteRegistryValue` | Delete a value |
| `createRegistryKey` | Create a key (no-op if it already exists) |

---

### `gt.xmlutils`

Thin helpers around `xml.etree.ElementTree`.

| Symbol | Description |
|---|---|
| `getRoot` | Parse an XML file and return the root element |
| `createRoot` | Create a new root element |
| `createSubelement` | Append a child element |
| `getChildrenRecursive` | Walk all descendants |
| `filterNodeList` | Filter a node list by tag or attribute |
| `find` | Find a direct child matching a predicate |
| `findRecursive` | Find any descendant matching a predicate |
| `prettyPrintElement` | Indent an element tree in-place |
| `writeFile` | Write an element tree to an XML file |

---

## Environment Variables

| Variable | Module | Description |
|---|---|---|
| `NET_STORAGE_MAP` | `gt.pycore` | JSON object mapping UNC prefixes to drive letters |

---

## License

See [LICENSE](LICENSE).
