#!/bin/bash
set -e

FORMATTER=clang-format-6.0
$FORMATTER --version

FORMATTING_ERRORS=0
SOURCE_FILES=`find ./redeem -name \*.cpp -type f -or -name \*.h -type f`
for SOURCE_FILE in $SOURCE_FILES
do
  export FORMATTING_ISSUE_COUNT=`$FORMATTER -output-replacements-xml $SOURCE_FILE | grep offset | wc -l`
  if [ "$FORMATTING_ISSUE_COUNT" -gt "0" ]; then
	echo "Source file $SOURCE_FILE contains formatting issues. Please use $FORMATTER to resolve found issues."
	FORMATTING_ERRORS=1
	# Reformat this file
	$FORMATTER -i $SOURCE_FILE
	git diff $SOURCE_FILE
  fi
done
exit $FORMATTING_ERRORS
