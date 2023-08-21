import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;

public class SlidingLog implements MyRateLimiter{
    private static final long PERMITS_PER_MINUTE = 60;

    private final TreeMap<Long, Integer> requestLogCountMap = new TreeMap<>();
    @Override
    public boolean tryAcquire() {
        long currentTimestamp = LocalDateTime.now().toEpochSecond(ZoneOffset.UTC);
        int currentWindowCount = getCurrentWindowCount(currentTimestamp);
        if (currentWindowCount >= PERMITS_PER_MINUTE) {
            return false;
        }
        requestLogCountMap.merge(currentTimestamp, 1, Integer::sum);
        return false;
    }

    private int getCurrentWindowCount(long currentTime) {
        long startTime = currentTime - 59;
        return requestLogCountMap.entrySet()
                .stream()
                .filter(entry -> entry.getKey() >= startTime)
                .mapToInt(Map.Entry::getValue)
                .sum();
    }
}
