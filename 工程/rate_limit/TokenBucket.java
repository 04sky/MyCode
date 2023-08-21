import java.util.TreeMap;

public class TokenBucket implements MyRateLimiter{
    /**
     * 令牌桶容量
     */
    private final long capacity;
    /**
     * 令牌发放速率
     */
    private final long generatedPerSeconds;
    /**
     * 最后一个令牌发送时间
     */
    long lastTokenTime = System.currentTimeMillis();
    /**
     * 当前令牌数量
     */
    private long currentTokens;
    public TokenBucket(long capacity, long generatedPerSeconds) {
        this.capacity = capacity;
        this.generatedPerSeconds = generatedPerSeconds;
    }

    @Override
    public boolean tryAcquire() {
        long now = System.currentTimeMillis();
        if (now - lastTokenTime >= 1000) {
            long newPermits = (now - lastTokenTime) / 1000 * generatedPerSeconds;
            currentTokens = Math.min(currentTokens + newPermits, capacity);
            lastTokenTime = now;
        }
        if (currentTokens > 0) {
            currentTokens--;
            return true;
        }
        return false;
    }
}
