import java.util.*;

import static javax.swing.UIManager.get;

public class Twitter {
    private static int timestamp = 0;
    private static class User{
        private int id;
        public Set<Integer> followed;
        public Twit head;

        public User(int id) {
            this.id = id;
            followed = new HashSet<>();
            head = null;
            follow(id);
        }

        public void post(int tweetId){
            Twit twit = new Twit(tweetId, timestamp);
            timestamp++;
            twit.next = head;
            head = twit;
        }
        public void follow(int followId){
            followed.add(followId);
        }
        public void unfollow(int followId){
            if (followId != this.id) {
                followed.remove(followId);
            }
        }
    }
    private static class Twit{
        private int id;
        private int time;
        private Twit next;

        public Twit(int id, int time) {
            this.id = id;
            this.time = time;
            this.next = null;
        }
    }
    public HashMap<Integer, User> hashMap = new HashMap<>();

    /** Initialize your data structure here. */
    public Twitter() {

    }

    /** Compose a new tweet. */
    public void postTweet(int userId, int tweetId) {
        if (!hashMap.containsKey(userId)) {
            hashMap.put(userId, new User(userId));
        }
        hashMap.get(userId).post(tweetId);
    }

    /** Retrieve the 10 most recent tweet ids in the user's news feed. Each item in the news feed must be posted by users who the user followed or by the user herself. Tweets must be ordered from most recent to least recent. */
    public List<Integer> getNewsFeed(int userId) {
        List<Integer> res = new ArrayList<>();
        if (!hashMap.containsKey(userId)) {
            return res;
        }
        Set<Integer> users=  hashMap.get(userId).followed;
        PriorityQueue<Twit> pq = new PriorityQueue<>(users.size(), (a, b) -> (b.time - a.time));
        for (int i : users) {
            Twit twit = hashMap.get(i).head;
            if (twit==null)continue;
            pq.add(twit);
        }
        while(!pq.isEmpty()){
            if (res.size() == 10) {
                break;
            }
            Twit twit = pq.poll();
            res.add(twit.id);
            if (twit.next!=null) {
                pq.add(twit.next);
            }
        }
        return res;
    }

    /** Follower follows a followee. If the operation is invalid, it should be a no-op. */
    public void follow(int followerId, int followeeId) {
        if (!hashMap.containsKey(followerId)) {
            hashMap.put(followerId, new User(followerId));
        }
        if (!hashMap.containsKey(followeeId)) {
            hashMap.put(followeeId, new User(followeeId));
        }
        hashMap.get(followerId).follow(followeeId);
    }

    /** Follower unfollows a followee. If the operation is invalid, it should be a no-op. */
    public void unfollow(int followerId, int followeeId) {
        if (hashMap.containsKey(followerId)) {
            hashMap.get(followerId).unfollow(followeeId);
        }
    }
}