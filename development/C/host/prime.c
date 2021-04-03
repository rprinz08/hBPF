#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>


bool prime(uint64_t arg) {

    for(int64_t i = 2; i < arg; i++)
        if (arg % i == 0)
            return false;

    return true;
}


int main(int argc, char **argv)
{
    int n = 9;
    if(argc > 1)
        n = atoi(argv[1]);
    bool p = prime(n);
    printf("n=%d, is_prime=%d\n", n, p);
    //getchar();
    return 0;
}

