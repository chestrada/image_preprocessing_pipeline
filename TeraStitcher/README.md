TeraStitcher
===========================================================

A tool for fast automatic 3D-stitching of teravoxel-sized 
microscopy images (BMC Bioinformatics 2012, 13:316)

Exploiting multi-level parallelism for stitching very large 
microscopy images (Frontiers in Neuroinformatics, 13, 2019)

===========================================================

Before using this software, you MUST accept the LICENSE.txt

Documentation,  help and  other info  are available on  our 
GitHub wiki at http://abria.github.io/TeraStitcher/.

===========================================================

Contributors

- Alessandro Bria (email: a.bria@unicas.it).
  Post-doctoral Fellow at University of Cassino (Italy).
  Main developer.

- Giulio Iannello (email: g.iannello@unicampus.it).
  Full Professor at University Campus Bio-Medico of Rome (italy).
  Supervisor and co-developer.
  
===========================================================

Main features

- designed for images exceeding the TeraByte size
- fast and reliable 3D stitching based on a multi-MIP approach
- typical memory requirement below 4 GB (8 at most)
- 2D stitching (single slice images) supported
- regular expression based matching for image file names
- data subset selection
- sparse data support
- i/o plugin-based architecture
- stitching of multichannel images
- support for big tiff files (> 4 GB)
- HDF5-based formats
- parallelization on multi-core platform
- fast alignment computation on NVIDIA GPUs

===========================================================

### GPU acceleration

install cuda and set cuda and java environment variables.

```bash
# CUDA
export CUDA_ROOT_DIR=/usr/local/cuda/
export PATH=${PATH}:${CUDA_ROOT_DIR}/bin
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${CUDA_ROOD_DIR}/lib64

# Java
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:"/usr/lib/jvm/java-11-openjdk-amd64/lib/server/"

# export HDF5_DIR=/path/to/mcp3d/src/3rd_party/hdf5

mkdir build && cd build
```
For CUDA 11 and newer GPUs, in addition to [original compilation documentation instructions](https://github.com/abria/TeraStitcher/wiki/Get-and-build-source-code) do the following:
edit `/path/to/TeraStitcher/src/crossmips/CMakeLists.txt` and change `-arch sm30` to `-arch sm60`

`
cmake ../src/ -DWITH_UTILITY_MODULE_mergedisplacements:BOOL="1" -DWITH_CUDA:BOOL="1" -DWITH_UTILITY_MODULE_terastitcher2:BOOL="1" -DWITH_HDF5:BOOL="0" -DWITH_IO_PLUGIN_IMS_HDF5:BOOL="0" -DWITH_UTILITY_MODULE_example:BOOL="0" -DWITH_IO_PLUGIN_bioformats2D:BOOL="0" -DWITH_UTILITY_MODULE_pyscripts:BOOL="0" -DWITH_UTILITY_MODULE_subvolextractor:BOOL="1" -DWITH_NEW_MERGE:BOOL="1" -DWITH_UTILITY_MODULE_teraconverter:BOOL="1" -DWITH_UTILITY_MODULE_virtualvolume:BOOL="1" -DWITH_RESUME_STATUS:BOOL="1" -DWITH_UTILITY_MODULE_mdatagenerator:BOOL="1" -DCMAKE_INSTALL_PREFIX="../install" -DCMAKE_C_FLAGS="-Ofast -march=native -fomit-frame-pointer -mfpmath=both -pipe -fPIC -frecord-gcc-switches -flto -w" -DCMAKE_CXX_FLAGS="-Ofast -march=native -fomit-frame-pointer -mfpmath=both -pipe -fPIC -frecord-gcc-switches -flto -w" && make -j20
`

copy the binaries to appropriate folders