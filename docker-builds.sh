#! /bin/bash

for arch in centos6-i386 centos6-x86_64 centos7-x86_64 ubuntu-i386 ubuntu-amd64; do
    (docker run --rm -t -v $(pwd):/toopher-pam toopher/toopher-pam-builder:$arch) &
done

wait
