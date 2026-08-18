import json
import os
import tweepy
import yfinance as yf

# X API 認証（環境変数から取得）
client = tweepy.Client(
    consumer_key=os.environ["X_CONSUMER_KEY"],
    consumer_secret=os.environ["X_CONSUMER_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"]
)

def build_tweets(symbols):
    """
    株価情報を取得し、140文字以内に収まるようツイート本文を複数に分割する関数
    """
    header = "【株価速報】\n"
    tweets = []
    current_tweet = header

    for item in symbols:
        try:
            ticker = yf.Ticker(item["code"])
            df = ticker.history(period="2d")
            
            if len(df) >= 2:
                prev_close = df["Close"].iloc[-2]     # 前営業日終値
                current_price = df["Close"].iloc[-1]  # 最新株価
                
                diff = current_price - prev_close
                pct_change = (diff / prev_close) * 100
                
                sign = "▲" if diff > 0 else "▼" if diff < 0 else "─"
                line = f"{item['name']}: {current_price:,.1f}円 ({sign}{abs(pct_change):.2f}%)\n"
                
                if len(current_tweet + line) > 130:
                    tweets.append(current_tweet.strip())
                    current_tweet = "【株価速報 続き】\n" + line
                else:
                    current_tweet += line
        except Exception as e:
            print(f"Error fetching {item['name']}: {e}")

    if current_tweet.strip():
        tweets.append(current_tweet.strip())

    return tweets

def main():
    with open("symbols.json", "r", encoding="utf-8") as f:
        symbols = json.load(f)

    tweets = build_tweets(symbols)

    if not tweets:
        print("投稿するデータがありませんでした。")
        return

    previous_tweet_id = None

    for i, tweet_text in enumerate(tweets):
        try:
            if previous_tweet_id is None:
                response = client.create_tweet(text=tweet_text)
            else:
                response = client.create_tweet(
                    text=tweet_text,
                    in_reply_to_tweet_id=previous_tweet_id
                )
            
            previous_tweet_id = response.data['id']
            print(f"ツイート {i+1}/{len(tweets)} 投稿成功！")
            
        except Exception as e:
            print(f"ツイート {i+1} の投稿エラー: {e}")

if __name__ == "__main__":
    main()
