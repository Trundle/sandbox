
#ifndef _COM_GUID_HPP_
#define _COM_GUID_HPP_

#define COM_NO_WINDOWS_H
#include <unknwn.h>

namespace com
{
const GUID IID_class_wrapper = { 0x3141bc3b, 0x113d, 0x4c29, 
    { 0x94, 0x3f, 0x35, 0x30, 0x40, 0x3e, 0x7d, 0x76 } };   // {3141BC3B-113D-4c29-943F-3530403E7D76}
const GUID IID_fundamental_wrapper = { 0x7e2eb07a, 0x3203, 0x433b, 
    { 0x94, 0x6, 0x3e, 0x10, 0xef, 0xb, 0xd3, 0xaf } };     // {7E2EB07A-3203-433b-9406-3E10EF0BD3AF}
} // namespace com

#endif // _COM_GUID_HPP_
