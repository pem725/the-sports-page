"""
almanac_data.py — historical facts for the Almanac block.

Each of the five anniversary years (1776, 1826, 1876, 1926, 1976) gets a
pool of year-level facts. The almanac block picks one fact per year per
issue, rotated by issue number, so consecutive issues see different facts.

For 500 issues across these 5 years, we want ~10-15 facts per year to
keep the rotation feeling fresh. Add more over time. Keep entries to one
sentence; the Almanac block is meant to be a brief footer, not a history
lesson.

Anniversary years are listed in chronological order (oldest first), which
is how they render in the block.
"""

ANNIVERSARIES = [
    {
        "year": 1776,
        "years_ago": 250,
        "facts": [
            "The Continental Congress sat in Philadelphia, debating whether thirteen colonies could become anything at all. The vote that mattered came on July 2.",
            "Thomas Paine's <em>Common Sense</em>, published in January, had sold over 100,000 copies by spring &mdash; the most-read pamphlet, per capita, in American history.",
            "George Washington was commanding an army that did not yet have a country.",
            "John Adams wrote his wife that future generations would remember &ldquo;the second day of July, 1776&rdquo; as the great anniversary. He was off by two days.",
            "The Declaration was signed on July 4 by John Hancock alone; most signatures came on August 2.",
            "British forces evacuated Boston in March and would land in New York harbor by July, with the largest fleet in human history to that point.",
            "Benjamin Franklin, age 70, sailed for Paris in October to secure French aid. He stayed eight years.",
            "Smallpox killed more Continental soldiers in 1776 than British muskets did.",
            "The Battle of Trenton (December 26) saved a revolution most Europeans had already written off.",
            "Virginia adopted its Declaration of Rights in June, the first state constitution in human history.",
        ],
    },
    {
        "year": 1826,
        "years_ago": 200,
        "facts": [
            "John Adams and Thomas Jefferson, the last surviving signers of the Declaration, both died on July 4 &mdash; fifty years to the day after independence. Adams's last words were reported to be &ldquo;Jefferson still survives.&rdquo; Jefferson had died five hours earlier.",
            "John Quincy Adams was president, having lost the popular vote to Andrew Jackson in 1824 and won the runoff in the House. Jackson would return for him in 1828.",
            "The Erie Canal, completed the year before, was reshaping continental commerce. Buffalo to New York City had become a 9-day trip.",
            "James Fenimore Cooper published <em>The Last of the Mohicans</em>, inventing the American historical novel.",
            "The American Temperance Society was founded in Boston. By 1834, it would claim a million members.",
            "Andrew Jackson was building the campaign that would, two years later, end the Era of Good Feelings.",
            "The country had 13 million people, 1.7 million of them enslaved. Slavery had been formally abolished in seven Northern states.",
            "The first US railroad &mdash; three miles of horse-drawn track in Quincy, Massachusetts &mdash; opened in October.",
            "Stephen Foster, who would write &ldquo;Oh! Susanna&rdquo; and &ldquo;Camptown Races,&rdquo; was born in July.",
            "President Adams proposed a national university and observatory. Congress refused. The country was, even then, suspicious of federal ambition.",
        ],
    },
    {
        "year": 1876,
        "years_ago": 150,
        "facts": [
            "The presidential election that fall was decided not at the ballot box but by a fifteen-member electoral commission. Samuel Tilden (D) won the popular vote. Rutherford B. Hayes (R) was awarded the White House in exchange for ending Reconstruction.",
            "The Centennial Exposition opened in Philadelphia on May 10 and ran six months. About ten million Americans visited &mdash; one in four.",
            "Alexander Graham Bell received the patent for the telephone on March 7. He spoke the first audible sentence into it three days later.",
            "On June 25, George Custer and his Seventh Cavalry rode into a Lakota and Cheyenne village along the Little Bighorn River. None of them rode out.",
            "Mark Twain published <em>The Adventures of Tom Sawyer</em>. The sequel about Huck was eight years away.",
            "Heinz introduced ketchup. Anheuser-Busch introduced Budweiser. The first National League baseball season was played, won by the Chicago White Stockings.",
            "Colorado was admitted as the 38th state &mdash; the Centennial State &mdash; on August 1.",
            "Reconstruction was ending. Federal troops would leave the South in 1877 as part of the deal that put Hayes in office. The Compromise of 1877 set the terms for the next ninety years of American race relations.",
            "Wild Bill Hickok was shot dead holding aces and eights in Deadwood. The hand is now called &ldquo;the dead man's.&rdquo;",
            "Boss Tweed, the Tammany Hall machine politician who had stolen more public money than any American before him, was arrested in Spain after escaping a New York prison. He died in jail in 1878.",
        ],
    },
    {
        "year": 1926,
        "years_ago": 100,
        "facts": [
            "The Sesquicentennial International Exposition opened in Philadelphia in June, marking 150 years since the Declaration. It went broke. Most Americans, deep in the long Coolidge boom, found it easier to stay home.",
            "Calvin Coolidge was president, governing as little as he could and saying even less.",
            "Babe Ruth hit 47 home runs for the Yankees. Lou Gehrig hit 16. Together they remade what an offense could be.",
            "A.A. Milne published <em>Winnie-the-Pooh</em> in October. Christopher Robin was six.",
            "Robert Goddard launched the first liquid-fueled rocket in March, a 2.5-second flight that reached 41 feet over a Massachusetts farm.",
            "The Ku Klux Klan had perhaps five million members &mdash; the peak of the second-era Klan, which had been refounded a decade earlier and was now mainstream in much of the Midwest.",
            "Harry Houdini died on Halloween of peritonitis from a ruptured appendix, a few days after being punched in the stomach by a college student.",
            "Charles Jenkins demonstrated the first practical television in Washington, transmitting images over five miles. The picture was small, blurry, and roughly the future.",
            "Sinclair Lewis published <em>Elmer Gantry</em> the following year, but the manuscript &mdash; an attack on American religious hypocrisy &mdash; was already circulating in 1926.",
            "The country had 117 million people, 16 percent of them foreign-born. Immigration restriction had been federal law since 1924. The doors were closing.",
            "Gene Tunney took the heavyweight title from Jack Dempsey on points in Philadelphia. The rematch the next year drew $2.6 million at the gate.",
            "Notre Dame finished its football season 9-1, losing only to Carnegie Tech. Knute Rockne was 38.",
        ],
    },
    {
        "year": 1976,
        "years_ago": 50,
        "facts": [
            "The Bicentennial year. The Tall Ships sailed into New York harbor on July 4 for Operation Sail. Sixteen of them. The crowds were the largest the city had ever seen.",
            "Gerald Ford was president, having taken the office on Nixon's resignation two years earlier. He would lose to Jimmy Carter in November.",
            "Apple Computer was founded in April by two men in a garage in Cupertino. The Apple I sold for $666.66.",
            "The Concorde began commercial service in January, flying London-to-New York in 3.5 hours.",
            "Viking 1 landed on Mars on July 20 &mdash; seven years to the day after the Apollo 11 moon landing &mdash; and returned the first color photographs from the surface.",
            "Cincinnati's Big Red Machine won its second straight World Series, sweeping the Yankees in four. The roster included Bench, Rose, Morgan, and Perez.",
            "<em>Rocky</em> won Best Picture. <em>Network</em>'s Howard Beale gave the &ldquo;mad as hell&rdquo; speech. <em>All the President's Men</em> opened in April.",
            "Stevie Wonder released <em>Songs in the Key of Life</em> in September after two years of work. It debuted at #1.",
            "Saigon had fallen the previous spring. The country was still raw about it. Carter's campaign offered, more than anything else, the chance to look away.",
            "The unemployment rate averaged 7.7%. Inflation averaged 5.7%. The combination was called &ldquo;stagflation&rdquo; and was, until then, supposed to be impossible.",
            "Patty Hearst was convicted of bank robbery in March. The Symbionese Liberation Army was a fading memory.",
            "Jimmy Carter, a peanut farmer from Plains, Georgia who had been polling at 1% a year earlier, accepted the Democratic nomination in New York and went on to beat an incumbent.",
            "Bruce Springsteen was on his second album. He would not release a third until 1978.",
        ],
    },
]


def total_facts():
    """Diagnostic helper: how many facts are loaded total."""
    return sum(len(y["facts"]) for y in ANNIVERSARIES)


if __name__ == "__main__":
    print(f"Loaded {len(ANNIVERSARIES)} anniversary years with {total_facts()} total facts.")
    for y in ANNIVERSARIES:
        print(f"  {y['year']}: {len(y['facts'])} facts")
