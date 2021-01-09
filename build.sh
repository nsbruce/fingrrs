
source ~/Documents/envs/BH/bin/activate

pyinstaller --name 'Fingrrs Desktop' --onefile --hidden-import cmath --windowed --icon graphics/icon-1024x1024.icns cli.py