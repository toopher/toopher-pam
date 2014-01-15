#!/bin/bash
#
# Build the release directory for the web, and the .orig.tar.gz
# for the debian package.
#
set -e

ME=$(basename $PWD)
PACKAGE=$(tr <<<"${ME%-*}" - _)
VERSION=${ME##*-}
YEAR=$(date +%Y)
MONTH=$(date +%b)
DATE=$(date +%Y-%m-%d)

#
# Update all the version numbers and dates.
#
sed -i "/${YEAR}/!s/^\( [*].*Copyright (c) .*2[0-9]*\)\([ ]*Russell Stuart\)/\1,${YEAR}\2/" src/${PACKAGE}.c
sed -i "s/^\(\(static \+\)\?\(const \+\)\?char .*_version..[ 	]*=[ 	]*\"\)[^\"]*/\1${VERSION}/" src/${PACKAGE}.c
sed -i "s/^\(\(static \+\)\?\(const \+\)\?char .*_date..[ 	]*=[ 	]*\"\)[^\"]*/\1${DATE}/" src/${PACKAGE}.c
sed -i "/${YEAR}/!s/\(.* is copyright &copy; .*2[0-9]*\)\([ ]*Russell Stuart\)/\1,${YEAR}\2/" ${PACKAGE}.html
sed -i "s/${PACKAGE}-[0-9]\+[.][0-9]\+[.][0-9]\+/${ME}/g" ${PACKAGE}.html
sed -i "s/${ME%-*}-[0-9]\+[.][0-9]\+[.][0-9]\+/${ME}/g" ${PACKAGE}.html
sed -i "/${YEAR}/!s/^\( *Copyright (c) .*2[0-9]*\)\([ ]*Russell Stuart\)/\1,${YEAR}\2/" README.txt
sed -i "s/^\(\(version\|release\) *= *\).*/\1'${VERSION}'/" doc/conf.py

#
# Clean up.
#
debian/rules clean
make doc

#
# Build the www directory.
#
rm -rf "${PACKAGE}"
mkdir -p "${PACKAGE}"
(cd ..; tar cfz "${ME}/${PACKAGE}/${ME}.tar.gz" --exclude="${ME}/debian" --exclude="${ME}/${PACKAGE}" --exclude="${ME}/.pc" "${ME}")
cp ChangeLog.txt README.txt epl-v10.html "${PACKAGE}.html" "${PACKAGE}"
cp -a doc/html "${PACKAGE}/doc"
cp -a examples "${PACKAGE}"
ln -s "${PACKAGE}.html" "${PACKAGE}/index.html"
cp "${PACKAGE}/${ME}.tar.gz" "../${ME%-*}_${VERSION}.orig.tar.gz"
