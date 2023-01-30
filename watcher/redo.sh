#!/bin/bash


rm -rf ./importer*
rm -rf ./processor_*
rm -rf ./exporter_*
rm metadata.json

$HOME/go/src/github.com/algorand/indexer/cmd/conduit/conduit -d .

