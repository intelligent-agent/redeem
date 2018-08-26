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

#include <chrono>
#include <ctime>
#include <iostream>
#include <mutex>
#include <sstream>

class Logger
{
private:
    static std::mutex coutMutex;

    std::unique_lock<std::mutex> lock;

public:
    Logger()
        : lock(coutMutex)
    {

        std::chrono::time_point<std::chrono::system_clock> timestamp = std::chrono::system_clock::now();

        std::cerr << "[ " << std::chrono::duration_cast<std::chrono::milliseconds>(timestamp.time_since_epoch()).count()
                  << " ]\t";
    }

    template <typename TToken>
    Logger& operator<<(const TToken& s)
    {
        std::cerr << s;

        return *this;
    }

    // this is the type of std::cout
    typedef std::basic_ostream<char, std::char_traits<char>> CoutType;

    // this is the function signature of std::endl
    typedef CoutType& (*StandardEndLine)(CoutType&);

    // define an operator<< to take in std::endl
    Logger& operator<<(StandardEndLine manip)
    {
        // call the function, but we cannot return it's value
        manip(std::cerr);

        return *this;
    }

    virtual ~Logger()
    {
    }
};

// LOGLEVEL is defined in setup.py

#define LOGLEVEL_CRITICAL 50
#define LOGLEVEL_ERROR 40
#define LOGLEVEL_WARNING 30
#define LOGLEVEL_INFO 20
#define LOGLEVEL_DEBUG 10
#define LOGLEVEL_NOTSET 0

#ifndef LOGLEVEL
#define LOGLEVEL LOGLEVEL_WARNING
#endif

#if LOGLEVEL <= LOGLEVEL_CRITICAL
#define LOGCRITICAL(x) Logger() << "CRITICAL " << x
#else
#define LOGCRITICAL(x)
#endif

#if LOGLEVEL <= LOGLEVEL_ERROR
#define LOGERROR(x) Logger() << "ERROR    " << x
#else
#define LOGERROR(x)
#endif

#if LOGLEVEL <= LOGLEVEL_WARNING
#define LOGWARNING(x) Logger() << "WARNING  " << x
#else
#define LOGWARNING(x)
#endif

#if LOGLEVEL <= LOGLEVEL_INFO
#define LOGINFO(x) Logger() << "INFO     " << x
#else
#define LOGINFO(x)
#endif

#if LOGLEVEL <= LOGLEVEL_DEBUG
#define LOG(x) Logger() << "DEBUG    " << x
#else
#define LOG(x)
#endif

#endif /* defined(__PathPlanner__Logger__) */
