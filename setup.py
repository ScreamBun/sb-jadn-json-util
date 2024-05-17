from setuptools import setup, find_packages
 
setup(
    name="jadn-json",
    version="1.1.0", 
    packages=["jadnjson", "jadnjson.generators", "jadnjson.constants", "jadnjson.utils", "jadnjson.validators"],
    install_requires=[
        "Faker",
        "jsf",
        "jsonpointer",
        "jsonschema",
        "python-benedict"
    ]    
)