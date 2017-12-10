all:
	g++ *.cpp *.c `pkg-config --libs --cflags python` -DLOGLEVEL=10 -pthread -DDEMO_PRU -g -Og  #-fsanitize=float-divide-by-zero
