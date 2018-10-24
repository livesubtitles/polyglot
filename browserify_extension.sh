while read F  ; do
        browserify build/src/$F -o build/src/$F
done < $1
