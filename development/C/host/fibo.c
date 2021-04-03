#include <stdio.h>
#include <stdlib.h>

unsigned long fib(int n)
{
    unsigned long a = 0, b = 1, c, i;
    if (n == 0)
        return a;
    for (i = 2; i <= n; i++) {
        c = a + b;
        a = b;
        b = c;
    }
    return b;
}

int main(int argc, char **argv)
{
    int n = 9;
    if(argc > 1)
        n = atoi(argv[1]);
    unsigned long f = fib(n);
    printf("n=%d, fib=%lu (0x%016lx)\n", n, f, f);
    //getchar();
    return 0;
}

