# README

This piece of code demonstrates a small http web server providing a REST API endpoint in stream mode to calculate the sum of a list of integers

* endpoint
    * /total/
        * method: post
        * payload: [1, 2, 3, 4]
            * a list of integers in json format. Other format or number type may cause an error message.
        * response: { "total": 10 }
            * a dictionary which contains a key named "total" whose value is the sum, in json format.

The latest commit made a change to use ThreadPool to handle computations, which may improve the homogeneity of delay among all the simultaneous computation requests. The simple requests will not necessarily be delayed. However, the global delay will stay the same within the same process.

## Prerequisites

* It has been implemented on Mac OS X, but due to the limitation of tornado framework, please run it on a Linux host so as to have its full features. To make the whole thing hassle free, it is advised to use docker directly instead. To know more details, please check the info below.
* The tested python version is 3.6. Normally, it should have been defined by the embedded Dockerfile which makes you out of concern.

### How to install? ###

* On a work station directly
    * Install python dependencies
        ```bash
        pip install -r requirements.txt
        ```
    * Install using setup.py
        ```bash
        python setup.py install
        ```
* Using container tool
    * Build docker image
        ```bash
        docker build -t sum_cal .
        ```

### How to use? ###

* Launch the web server after a successful installation using the following command

    ```bash
    calsum --http-address=0.0.0.0 --app-debug=false --enable-auto-fork
    ```

* Launch it using a docker desktop

    ```bash
    docker-compose -f docker-compose.yml build
    docker-compose -f docker-compose.yml up
    ```

* Test it with a small python snippet
  * a long calculation
    ```python
    import requests
    import json
    r = requests.post("http://localhost:8000/total/", data=json.dumps(list(range(10000001))))
    print(r.json())
    ```
    expected output
    ```json
    {'total': 50000005000000}
    ```
  * some calculation requests in parallel
    ```python
    import requests
    import json
    from multiprocessing import Pool
    
    
    def test_request(x):
        r = requests.post("http://localhost:8000/total/", data=json.dumps(list(range(100001+x))))
        return json.loads(r.content.decode()).get("total")
    
    def gen_result(x):
        return sum(range(100001 + x))
    
    with Pool(10) as p:
        expected = [gen_result(x) for x in range(100)]
        for e, r in zip(expected, p.map(test_request, [_ for _ in range(100)])):
            if e != r:
                raise Exception("{}!={}".format(e, r))
        print("ok at this scale")
    ```
    expected output
    ```bash
    ok at this scale
    ```

### How to develop? ###

* Install dependencies
    ```bash
    pip install -r requirements.txt
    ```

* Install in development mode and run the server
    ```bash
    python setup.py develop
    calsum --http-address=0.0.0.0 --app-debug=true
    ```

* Run tests
    ```bash
    python setup.py test
    ```
