all:
	cp -r webextension/* build
	./browserify_extension.sh browserifiable_files
clean:
	rm -r build
