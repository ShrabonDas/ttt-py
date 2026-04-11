FROM python:3.10

SHELL ["/bin/bash", "-c"]

RUN apt update && apt install -y sbcl expect ripgrep

WORKDIR /root
RUN curl -O https://beta.quicklisp.org/quicklisp.lisp

RUN sbcl --load quicklisp.lisp \
         --eval "(quicklisp-quickstart:install)" \
         --eval "(quit)"
         
RUN echo '#-quicklisp(let ((ql-init (merge-pathnames "quicklisp/setup.lisp" (user-homedir-pathname)))) (when (probe-file ql-init) (load ql-init)))' >> /root/.sbclrc

WORKDIR /root/quicklisp/local-projects/

CMD ["bash"]