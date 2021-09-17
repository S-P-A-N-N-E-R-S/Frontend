echo "----- Script to build shared object -----"
echo "----- Start build -----"

echo "----- Try to delete existing .so file -----"
sudo rm /usr/lib/python3/dist-packages/AStarC.*.so

echo "----- Execute setup.py -----"
python3 scripts/setup.py build_ext --inplace

echo "----- Copy .so file into dist-packages -----"
sudo cp AStarC.*.so /usr/lib/python3/dist-packages

echo "----- Remove .so file from model directory -----"
rm AStarC.*.so
echo "----- Remove created .c file from model directory -----"
rm -r build

echo "----- End build -----"
echo "----- Restart QGIS so the shared object can be found -----"
