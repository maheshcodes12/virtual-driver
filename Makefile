CC=gcc

all:
	$(CC) src/vpbackend.c -o virtprinter
	$(CC) src/vpfilter.c -o vpfilter

install:
	sudo install -o root -g root -m 0555 virtprinter /usr/lib/cups/backend/virtprinter
	sudo install -o root -g root -m 0555 vpfilter /usr/lib/cups/filter/vpfilter
	sudo cp ppd/mahesh-virtual-printer.ppd /usr/share/ppd/

clean:
	rm -f virtprinter vpfilter
