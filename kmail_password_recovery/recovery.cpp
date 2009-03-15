#include <iostream>

#include <qstring.h>


QString decrypt(const QString &aStr)
{
    QString result;
    for (unsigned int i = 0; i < aStr.length(); i++)
        result += (aStr[i].unicode() <= 0x21 ) ? aStr[i] :
		                            QChar(0x1001F - aStr[i].unicode());
    return result;
}


int main(int argc, char** argv)
{
    if (argc != 2)
    {
        std::cerr << "usage: ./recovery <password>" << std::endl;
	return 1;
    }

    QString pwd = QString::fromUtf8(argv[1]);
    std::cout << decrypt(pwd) << std::endl;
    return 0;
}

