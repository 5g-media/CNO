# O-CNO-arbitrator
O-CNO-arbitrator allocates resources on demand from a pool of resources shared across multiple services (e.g. UC1 and UC2 services). This is a utility based optimization algorithm which takes resources constraint, service priorities and service level agreements into account. For instance, O-CNO-arbitrator is responsible to allocate GPU(s) to different services based on their priority and QoE constraints. Unlike the O-CNO-predictive-optimizer, this O-CNO-arbitrator algorithm is active all the time and it reacts to requests in a real time fashion.
## Prerequisites
- python3
- kafka
## Running
```
$ python3 o-cno.py
```
O-CNO-arbitrator is waiting for requests from different services and making a decision on allocating resources to them.
## Authors
- Truong Khoa Phan t.phan@ucl.ac.uk
## Acknowledgements
This project has received funding from the European Union’s Horizon 2020 research and innovation programme under grant agreement No 761699. The dissemination of results herein reflects only the author’s view and the European Commission is not responsible for any use that may be made of the information it contains.
## License
This project is licensed under the Apache 2.0 License
