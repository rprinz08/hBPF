#include <stdbool.h>

bool function(unsigned long int arg) {

    for(unsigned long int i = 2; i < arg; i++)
        if (arg % i == 0)
            return false;

    return true;
}
