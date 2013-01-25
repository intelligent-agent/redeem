
CFLAGS=-Wall -Iapp_loader/include -I/usr/include/python2.7 -D__DEBUG -O2 -mtune=cortex-a8 -march=armv7-a -shared -fPIC
LDFLAGS=-Lapp_loader/lib -lprussdrv -lpthread -fPIC
OBJ=pypruss.o
TARGET=pypruss.so

.PHONY: clean all install

all: $(TARGET)

$(OBJ)/%.o: %.c
	gcc $(CFLAGS) -c -o $@ $< 

$(TARGET): $(OBJ)
	gcc $(CFLAGS) -o $@ $^ $(LDFLAGS)


clean: 
	rm -rf $(OBJ) *~ $(TARGET)

install: 
	cp $(TARGET) /usr/lib/python2.7/site-packages/


