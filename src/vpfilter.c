#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <signal.h>

#define BUF_SIZE 65536

int main(int argc, char *argv[]) {
    signal(SIGPIPE, SIG_IGN);

    if (argc < 6) {
        fprintf(stderr, "ERROR: Invalid filter arguments\n");
        return 1;
    }

    const char *job_id = argv[1];
    const char *user = argv[2];
    const char *title = argv[3];
    const char *copies = argv[4];
    const char *options = argv[5];

    fprintf(stderr, "INFO: vpfilter started\n");
    fprintf(stderr, "INFO: job_id=%s user=%s title=%s copies=%s options=%s\n",
            job_id, user, title, copies, options);

    FILE *in = stdin;

    if (argc >= 7 && argv[6] && strlen(argv[6]) > 0) {
        in = fopen(argv[6], "rb");
        if (!in) {
            fprintf(stderr, "ERROR: Cannot open input file %s: %s\n", argv[6], strerror(errno));
            return 1;
        }
    }

    unsigned char buffer[BUF_SIZE];

    while (1) {
        size_t n = fread(buffer, 1, sizeof(buffer), in);

        if (n > 0) {
            if (fwrite(buffer, 1, n, stdout) != n) {
                fprintf(stderr, "ERROR: Cannot write to stdout\n");
                if (in != stdin) fclose(in);
                return 1;
            }
        }

        if (n < sizeof(buffer)) {
            if (feof(in)) break;
            if (ferror(in)) {
                fprintf(stderr, "ERROR: Cannot read input\n");
                if (in != stdin) fclose(in);
                return 1;
            }
        }
    }

    if (in != stdin) fclose(in);
    fflush(stdout);

    fprintf(stderr, "INFO: vpfilter completed\n");
    return 0;
}
