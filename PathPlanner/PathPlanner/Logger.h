//
//  Logger.h
//  PathPlanner
//
//  Created by Mathieu on 30.05.14.
//  Copyright (c) 2014 Xwaves. All rights reserved.
//

#ifndef __PathPlanner__Logger__
#define __PathPlanner__Logger__

#include <iostream>
#include <mutex>
#include <chrono>
#include <ctime>
#include <sstream>

class Logger {
private:
	static std::mutex coutMutex;
	
	std::stringstream internalStream;
	
public:
	
	Logger()  {
		auto timestamp = std::chrono::steady_clock::now();
		
		internalStream << "[ " <<  std::chrono::duration_cast<std::chrono::milliseconds>(timestamp.time_since_epoch()).count()
		<< " ]\t";
	}
	
	template <typename TToken>
	Logger& operator << (const TToken& s) {
		internalStream << s;
		
		return *this;
	}
	
	// this is the type of std::cout
	typedef std::basic_ostream<char, std::char_traits<char> > CoutType;
	
	// this is the function signature of std::endl
	typedef CoutType& (*StandardEndLine)(CoutType&);
	
	// define an operator<< to take in std::endl
	Logger& operator<<(StandardEndLine manip)
	{
		// call the function, but we cannot return it's value
		manip(internalStream);
		
		return *this;
	}
	
	virtual ~Logger() {
		std::unique_lock<std::mutex> lk(coutMutex);
		std::cout << internalStream.str();
	}
};

#define logger Logger()

#endif /* defined(__PathPlanner__Logger__) */
