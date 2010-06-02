#!/bin/bash

# textopdf.cgi
#
# textopdf.cgi is a little bash script to convert LaTeX files to PDF. Users may
# upload LaTeX files via a HTML form to a server and textopdf.cgi converts the
# LaTeX files to PDF and returns the PDF file.
#
# TODO: The prepartion of the LaTeX file is a little hackish. One may want fix
# this.
#
# Author: Sebastian Ramacher, 2010

LATEX=pdflatex -halt-on-error

function die_error()
{
    cat << EOF
Content-Type: text/plain

ERROR: $*
EOF
    exit;
}

if [ $REQUEST_METHOD != "POST" ]
then
    die_error "not a POST request";
fi

ctype=`echo $CONTENT_TYPE | sed 's/^\(.*\); .*$/\1/'`
# boundary=`echo $CONTENT_TYPE | sed 's/.* boundary=\(.*\)$/\1/'`

if [ $ctype != "multipart/form-data" ]
then
    die_error "invalid form data";
fi

# create temporary directory and prepare tex file
dir=`mktemp -d` || die_error "failed to create temporary directory"
file=$dir/input.tex
cat | tail -n +9 | head -n -1 > $file || \
    (rm -rf $dir && die_error "failed to create TeX file")

(cd $dir && $LATEX $file && $LATEX $file) > /dev/null || \
    (rm -rf $dir && die_error "failed to create PDF file")

# output the PDF
echo "Content-Type: application/pdf"
echo "Content-Disposition: attachment; filename=output.pdf"
echo ""
cat $dir/input.pdf

# clean up
rm -rf $dir
