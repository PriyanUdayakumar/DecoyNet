idf_component_register(SRCS "main.c"
                    INCLUDE_DIRS "."
                    REQUIRES esp8266 wifi http_server esp-tls)