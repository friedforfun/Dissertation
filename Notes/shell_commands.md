# Distiller

## compress_classifier params
 #### `-arch <>` resnet/cifar params:
See distiller/models/__init__.py

#### `-p=<int>` print frequency param

#### `--lr=<float>` initial learning rate

#### `--epochs=<int>` total number of epochs to run (default 90)

#### `--compress=<path>` configuration file for pruning the model (default is to use hard-coded schedule)

#### `-j=<int>` number of data loading workers (default 4)

#### `--deterministic` Ensure deterministic execution for re-producible results.

#### `--export-onnx` export model to ONNX format



### Resnet20 baseline trained on cifar dataset
From the intel distiller repository root:

`.../distiller $ time python examples/classifier_compression/compress_classifier.py --arch resnet20_cifar data.cifar10 -p=50 --lr=0.03 --epochs=180 --compress=examples/baseline_networks/cifar/resnet20_cifar_baseline_training.yaml -j=1 --deterministic --export-onnx`



# OpenVino
## Benchmark page:
[Link to some openvino benchmarking commands](https://software.intel.com/content/www/us/en/develop/articles/intel-neural-compute-stick-2-and-open-source-openvino-toolkit.html)

![Openvino benchmark](OpenvinoBenchmark.png)


## Prepare model optimizer

[Link to openvino config scripts doc](https://docs.openvinotoolkit.org/latest/openvino_docs_MO_DG_prepare_model_Config_Model_Optimizer.html)


## import & convert ONNX

1. Activate OpenVino env
2. Run:
    `.../openvino $ python /opt/intel/openvino_2021/deployment_tools/model_optimizer/mo_onnx.py --input_model ../distiller/path_to.onnx `


## Run built in benchmark tool

1. Activate Benchmark env
2. Run:
    `.../openvino $ python inference-engine/tools/benchmark_tool/benchmark_app.py -m <Path-to-model (can be .onnx)> -i <Path to images> -d 'MYRIAD'`