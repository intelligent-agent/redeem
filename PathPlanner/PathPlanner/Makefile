TARGET  := pathplanner.so
SRCS    := Path.cpp		PathPlanner.cpp		PathPlanner_wrap.cpp	Printer.cpp		PruTimer.cpp

OBJS    := ${SRCS:.cpp=.o} 
DEPS    := ${SRCS:.cpp=.dep} 
XDEPS   := $(wildcard ${DEPS}) 


SRC_C = prussdrv.c
             

OBJS_C    := ${SRC_C:.c=.o} 


CFLAGS = -I/usr/include/python2.7 -I/usr/include/python2.7/config

CCFLAGS = ${CFLAGS} -std=c++0x 

#LDFLAGS = 

.PHONY: all clean distclean 

all:: ${TARGET}

ifneq (${XDEPS},) 
include ${XDEPS} 
endif 


${TARGET}: ${OBJS} ${OBJS_C} 
	ld -shared $(OBJS) $(OBJS_C) -o $(TARGET) -lstdc++

${OBJS_C}: %.o: %.c
	$(CC) ${CFLAGS} -o $@ -c $< 

${OBJS}: %.o: %.cpp %.dep 
	$(CC) ${CCFLAGS} -o $@ -c $< 


${DEPS}: %.dep: %.cpp 
	$(CC) ${CCFLAGS} -MM $< > $@ 

clean:: 
	-rm -f *~ *.o ${TARGET} ${OBJS} ${OBJS_C} ${DEPS} converter_3d

distclean:: clean
