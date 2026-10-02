





for /l %%i in (60,10,80) do (
    python main.py --entity pod  --lamb %%i  --beta 0.7
)

  python main.py --entity pod    --beta 0.7
  python main.py --entity node   --beta 0.7
  python main.py --entity service   --beta 0.7