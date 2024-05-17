FROM postgres:15
ARG REPL_USER
ARG REPL_PASSWORD
ARG DATABASE
COPY init.sql /init.sql
RUN sed -i 's/replDATABASE/'"$DATABASE"'/g' /init.sql
RUN sed -i 's/replREPLUSER/'"$REPL_USER"'/g' /init.sql
RUN sed -i 's/replPASS/'"$REPL_PASSWORD"'/g' /init.sql

RUN mv init.sql /docker-entrypoint-initdb.d/

CMD [ "postgres" ]
