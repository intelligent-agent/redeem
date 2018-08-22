#pragma once

class SyncCallback
{
public:
    virtual ~SyncCallback()
    {
    }
    virtual void syncComplete();
};