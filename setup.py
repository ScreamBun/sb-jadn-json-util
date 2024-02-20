from setuptools import setup, find_packages
 
setup(
    name="jadn-json",
    version="1.0.0", 
    packages=["jadnjson", "jadnjson.generators", "jadnjson.constants", "jadnjson.utils"],
    install_requires=[
        "jsf",
        "jsonpointer",
        "jsonschema",
        "python-benedict"
    ]    
)