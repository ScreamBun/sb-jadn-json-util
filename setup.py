from setuptools import setup, find_packages
 
setup(
    name="jadnjson",
    version="1.4.0", 
    packages=["jadnjson", "jadnjson.generators", "jadnjson.constants", "jadnjson.utils", "jadnjson.validators"],
    install_requires=[
        "Faker",
        "jsf",
        "jsonpointer",
        "jsonschema",
        "python-benedict"
    ]    
)