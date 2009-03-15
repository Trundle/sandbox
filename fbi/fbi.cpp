//
// A small brainfuck interpreter.
//

#include <fstream>
#include <iostream>
#include <map>
#include <string>
#include <vector>


class CellIterator
{
public:
    CellIterator() : index_(0) {};
   
    char& operator*();
    CellIterator& operator++();
    CellIterator& operator--();
protected:
    int index_;
    std::map<int, char> cells_;
};

char& CellIterator::operator*()
{
    return cells_[index_];
}

CellIterator& CellIterator::operator++()
{
    ++index_;
    return *this;
}

CellIterator& CellIterator::operator--()
{
    --index_;
    return *this;
}

class Interpreter
{
public:
    bool run(const std::string&);
protected:
    CellIterator cell_;
};


bool Interpreter::run(const std::string& code)
{
    // First generate jump tables
    std::vector<std::string::const_iterator> from;
    std::map<std::string::const_iterator,
            std::string::const_iterator> jumps;
    for (std::string::const_iterator it=code.begin(); it != code.end(); ++it)
    {
        switch (*it)
        {
            case '[':
                from.push_back(it);
                break;

            case ']':
                if (!from.size())
                    return false;
                jumps[from.back()] = it;
                from.pop_back();
        }
    }
    std::vector<std::string::const_iterator> call_stack;
    for (std::string::const_iterator it=code.begin(); it != code.end(); ++it)
        switch (*it)
        {
            case '<':
                ++cell_;
                continue;;

            case '>':
                --cell_;
                continue;

            case '+':
                ++*cell_;
                continue;

            case '-':
                --*cell_;
                continue;

            case '.':
                std::cout << *cell_;
                //std::cout.flush();
                continue;

            case ',':
                std::cin.get(*cell_);
                continue;

            case '[':
                if (!*cell_)
                    it = jumps[it];
                else
                    call_stack.push_back(it);
                continue;

            case ']':
                if (*cell_)
                    it = call_stack.back();
                else
                    call_stack.pop_back();
                continue;
        }
    return true;
}


int main(int argc, char *argv[])
{
    std::string code;
    if (argc != 2)
    {
        std::cerr << "Usage: fbi <codefile>" << std::endl;
        return 1;
    }
    
    // Read code
    std::ifstream instream(argv[1]);
    if (!instream.is_open())
    {
        std::cerr << "Could not open file!" << std::endl;
        return 1;
    }

    std::string line;
    while (!instream.eof())
    {
        std::getline(instream, line);
        code.append(line);
    }

    Interpreter interpreter;
    if (!interpreter.run(code))
        return 1;
    return 0;
}
