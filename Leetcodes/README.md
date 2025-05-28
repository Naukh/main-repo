# Notes
This file shows general info about setup and how to compile/ run cpp files.

# Compilation:
There are two ways to compile cpp files:
1. Using VSCode compiler (Ctrl+Shift+B), this will give option to choose from three compilers already set:
    a. Clang++
    b. GCC
    c. MSVC
Note: This option doesn't work properly if mulitple cpp files with main functions are part of same directory.

2. Using termianl commands:
    a. Clang++: `clang++ .\name_of_code_file.cpp -o name_of_exe_file`
    b. GCC: `g++ name_of_code_file.cpp -o name_of_exe_file`
    c. MSVC: `cl name_of_code_file.cpp /Fe:name_of_exe_file.exe`
Note: This option works even if there exists multiple cpp files with main functions exist in same directory.

# Run:
To run the compile code, one can simply use terminal command `./name_of_exe_file` in command terminal.
