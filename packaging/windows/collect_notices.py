from importlib.metadata import distributions
from pathlib import Path
import shutil

root=Path("dist/Folder/licenses")
root.mkdir(parents=True,exist_ok=True)
versions=[]
for dist in distributions():
    name=dist.metadata["Name"]
    if not name:continue
    versions.append(f"{name}=={dist.version}")
    for entry in dist.files or []:
        if not any(x in entry.name.lower() for x in ("license","copying","notice")):
            continue
        source=Path(dist.locate_file(entry))
        if not source.is_file():continue
        target=root/name/str(entry).replace("/","_").replace("\\","_")
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
(root/"versions.txt").write_text("\n".join(sorted(versions)),encoding="utf-8")
