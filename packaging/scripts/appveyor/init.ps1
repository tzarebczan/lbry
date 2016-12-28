$env:Path += ";C:\MinGW\bin\"

$env:Path += ";C:\Program Files (x86)\Windows Kits\10\bin\x86\"

gcc --version

mingw32-make --version

C:\Python27\Scripts\pip.exe install "C:\projects\lbry\packaging\libs\win32\gmpy-1.17-cp27-none-win32.whl"

C:\Python27\Scripts\pip.exe install pypiwin32==219

# this is a patched to allow version numbers with non-integer values
# and it is branched off of 4.3.3
C:\Python27\Scripts\pip.exe install https://bitbucket.org/jobevers/cx_freeze/get/handle-version.tar.gz

cd C:\projects\lbry

C:\Python27\Scripts\pip.exe install -r requirements.txt
