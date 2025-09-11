using UnityEngine;
using UnityEngine.UI;  // 또는 TextMeshProUGUI 사용 시 using TMPro;
using SQLite;          // SQLite.cs 포함
using System.IO;
using System.Collections.Generic;
using TMPro;
using System;
using static CreateTable;

public class FavoriteDB_Controller : MonoBehaviour
{
    private SQLiteConnection db;
    public Button FavoriteButton;         // Inspector에서 연결
    public Sprite Sprite1;        // 바꿀 이미지 Sprite
    public Sprite Sprite2;        // 바꿀 이미지 Sprite
    public string NowChapterName;
    void Start()
    {
        //string NameDB = "hkData"+".db";
        string dbPath = Path.Combine(Application.persistentDataPath, "myDB.db");
        db = new SQLiteConnection(dbPath);

        //db.Execute("PRAGMA foreign_keys = ON;");

        //db.CreateTable<User>();
        //db.CreateTable<UserFavorite>();
        //db.CreateTable<FavoriteSelect>();
        //ShowFavorites();
    }

    // ✅ 버튼에 연결할 함수
    public void SQLiteDataAdd()
    {
        //InsertSampleUsers();
        InsertAminoFavorites();
        //ShowFavorites(); // UI 출력
    }

/*    void InsertSampleUsers()
    {
        if (db.Table<users>().Count() == 0)
        {
            db.Insert(new users
            {
                user_id = "localhost",
                username = "호스트",
                password = "localpass",
                email = "???@example.com",
                birth_date = "1990-01-01",
                department_name = "???과",
                grade = "?학년",
                created_at = System.DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
            });
        }
    }*/

    void InsertAminoFavorites()
    {
        var User = db.Table<users>()
                  .OrderBy(u => u.created_at)
                  .FirstOrDefault();

        string userId = User.user_id;      // 🔁 외부 입력값 사용
        string chapter = NowChapterName;

        var exists = db.Table<user_favorite>()
            .Where(f => f.user_id == userId && f.chapter_id == chapter)
            .FirstOrDefault();

        if (exists == null)
        {
            db.Insert(new user_favorite
            {
                user_id = userId,
                chapter_id = chapter
            });
            FavoriteButton.image.sprite = Sprite2;
        }
        else
        {
            Debug.Log("⚠️ 이미 해당 즐겨찾기가 존재합니다.");
            DeleteFavorite(userId, chapter);
            FavoriteButton.image.sprite = Sprite1;
        }
    }

    public void CheckAminoFavorites(string ChapterName)
    {
        var User = db.Table<users>()
                  .OrderBy(u => u.created_at)
                  .FirstOrDefault();

        NowChapterName = ChapterName;
        string userId = User.user_id;      // 🔁 외부 입력값 사용
        string chapter = ChapterName;

        var exists = db.Table<user_favorite>()
            .Where(f => f.user_id == userId && f.chapter_id == chapter)
            .FirstOrDefault();

        if (exists == null)
        {
            FavoriteButton.image.sprite = Sprite1;
        }
        else
        {
            FavoriteButton.image.sprite = Sprite2;
        }
    }

/*    void ShowFavorites()
    {
        List<UserFavorite> list = db.Table<UserFavorite>().ToList();
        string result = "즐겨찾기 목록\n";

        foreach (var fav in list)
        {
            result += $"{fav.user_id} | 챕터: {fav.chapter_num} | 페이지: {fav.page_id} | {fav.created_at}\n";
        }

        //uiText.text = result;
    }*/

    void DeleteFavorite(string userId, string chapter)
    {
        var favorite = db.Table<user_favorite>()
            .Where(f => f.user_id == userId && f.chapter_id == chapter)
            .FirstOrDefault();

        if (favorite != null)
        {
            db.Delete(favorite);
            Debug.Log("✅ 즐겨찾기 삭제 완료");
        }
        else
        {
            Debug.LogWarning("⚠️ 삭제할 즐겨찾기 항목이 없습니다.");
        }

        //ShowFavorites(); // UI 갱신
    }

    // 테이블 클래스는 동일하므로 그대로 유지
/*    public class User
    {
        [PrimaryKey]
        public string user_id { get; set; }

        [Indexed]
        public string username { get; set; }
        public string password { get; set; }
        public string email { get; set; }
        public string phone_number { get; set; }
        public string birth_date { get; set; }
        public string school_name { get; set; }
        public string department_name { get; set; }
        public bool auto_login { get; set; }
        public string created_at { get; set; }
    }

    public class UserFavorite
    {
        [PrimaryKey, AutoIncrement]
        public int id { get; set; }

        public string user_id { get; set; }
        public string chapter_num { get; set; }
        public string page_id { get; set; }
        public string created_at { get; set; }
    }

    public class FavoriteSelect
    {
        [PrimaryKey, AutoIncrement]
        public int id { get; set; }
        public string selectedText { get; set; }
    }*/
}
