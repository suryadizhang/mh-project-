#!/bin/bash
curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"suryadizhang.swe@gmail.com","password":"13Agustus!"}'
