echo "Script to build shared object with pybind"
echo "Start build"
echo "Execute setup.py"
python3 scripts/setup.py build_ext --inplace
echo "Copy .so file into dist-packages"
cp AStarC.*.so models/
echo "Remove .so file"
rm AStarC.*.so
echo "Remove build folder"
rm -r build
echo "End pybind build"
