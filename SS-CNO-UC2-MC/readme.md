# SS-CNO-UC2-MC
This SS-CNO UC2 Mobile Contribution is responsible for receiving a request from the edge-selector. It then makes a decision whether to serve the request using reserved resources or asking the O-CNO-arbitrator to use the shared resources pool.
## Prerequisites
- python3
- kafka
## Running
```
$ python3 o-cno-uc2_e2e_full.py
```
SS-CNO-UC2-MC is waiting for requests from the edge selector, after making a decision, it sends a reply to the edge-selector.
## Authors
Truong Khoa Phan t.phan@ucl.ac.uk
## Acknowledgements
This project has received funding from the European Union’s Horizon 2020 research and innovation programme under grant agreement No 761699. The dissemination of results herein reflects only the author’s view and the European Commission is not responsible for any use that may be made of the information it contains.
## License
This project is licensed under the Apache 2.0 License
