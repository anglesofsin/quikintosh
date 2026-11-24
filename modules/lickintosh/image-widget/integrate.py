from pathlib import Path
import sys
p=Path(sys.argv[1])/'ui/widgets/types/ImageWidget.qml';p.chmod(p.stat().st_mode|0o200);p.write_text((Path(__file__).parent/'ImageWidget.qml').read_text())
