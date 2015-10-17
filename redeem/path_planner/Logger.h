/*
 This file is part of Redeem - 3D Printer control software
 
 Author: Mathieu Monney
 Website: http://www.xwaves.net
 License: GNU GPLv3 http://www.gnu.org/copyleft/gpl.html
 
 Redeem is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.
 
 Redeem is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
 along with Redeem.  If not, see <http://www.gnu.org/licenses/>.
 
 */

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
		std::chrono::time_point<std::chrono::system_clock> timestamp = std::chrono::system_clock::now();
		
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
		std::cerr << internalStream.str();
	}
};

#ifndef NDEBUG
#define LOG(x) Logger() << x
#else
#define LOG(x) Logger() << x
#endif

#endif /* defined(__PathPlanner__Logger__) */
