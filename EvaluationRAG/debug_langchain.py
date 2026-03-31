import langchain
import os
import pkgutil

print(f"Version: {langchain.__version__}")
print(f"Path: {langchain.__file__}")

package_path = os.path.dirname(langchain.__file__)
print(f"Package Dir: {package_path}")

print("Submodules:")
for _, name, _ in pkgutil.iter_modules([package_path]):
    print(name)

try:
    import langchain.chains
    print("Import langchain.chains SUCCESS")
except ImportError as e:
    print(f"Import langchain.chains FAILED: {e}")
